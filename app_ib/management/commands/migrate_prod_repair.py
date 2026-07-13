"""One-time repair layer for the old-prod -> new-backend data migration.

Run ONCE, right after `migrate`, on a DB restored from the old prod dump
(see MIGRATION-PLAN.md). Each step backfills a new column/relation that the
pending migrations were supposed to populate but silently no-op on real prod
data shapes. Every step is idempotent against its own output; the command is
safe to re-run immediately, but is not meant as a recurring job (step 3 would
flip a deliberately-closed schedule created after cutover).
"""
import re
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F, Q
from django.utils.text import slugify

from app_ib.algorithms.completion import recompute_all_completion
from interior_advertisement.models import AdAsset, HomeHeroBanner
from interior_billing.models import (ArchitectPlan, AutomationPlan, BusinessPlan,
                                     PlanBillingCycle, ShopPlan, Subscription)
from interior_business.models import Business, DaySchedule
from interior_cms.models import StockMedia

_IMG_RE = re.compile(r'\.(jpe?g|png|webp|gif)(\?.*)?$', re.I)


def _dec(val):
    """'₹84,999' / '1,23,499' / 7999 -> Decimal; blank/garbage/<=0 -> None."""
    s = re.sub(r"[^\d.]", "", str(val or ""))
    if not s:
        return None
    try:
        d = Decimal(s)
    except InvalidOperation:
        return None
    return d if d > 0 else None


def _months(dur):
    """Any legacy duration shape -> months. Handles the real prod values that
    broke 0067: '1 year', '6 months', '90' (days), '3' (months), None."""
    s = str(dur or "").strip().lower()
    m = re.match(r"^(\d+(?:\.\d+)?)\s*([a-z]*)", s)
    if not m:
        return 0
    n, unit = float(m.group(1)), m.group(2)
    if unit.startswith("year") or unit in ("y", "yr", "yrs"):
        return int(n * 12)
    if unit.startswith("month") or unit in ("m", "mo", "mos"):
        return int(n)
    if unit.startswith("day") or unit == "d":
        return max(1, round(n / 30))
    n = int(n)
    if n >= 28:  # bare number: legacy days heuristic (matches 0067)
        return {90: 3, 180: 6, 365: 12, 730: 24}.get(n, max(1, round(n / 30)))
    return n


class Command(BaseCommand):
    help = "Backfill data stranded by the old-prod restore (see MIGRATION-PLAN.md)."

    @transaction.atomic
    def handle(self, *args, **opts):
        self._billing_cycles()      # gap 3
        self._business_slugs()      # gap 4
        self._day_schedules()       # gap 5
        self._plan_duration_months()  # gap 12
        self._completion()          # gap 11
        self._hero_images()         # gap 13
        self._ad_meta()             # gap 9
        self.stdout.write(self.style.SUCCESS("migrate_prod_repair: done"))

    def _log(self, msg):
        self.stdout.write(f"  {msg}")

    # gap 3 — money source of truth moved to PlanBillingCycle; 0067 created
    # nothing for plans whose duration is a word form ('1 year'). One cycle per
    # availableDuration entry; scalar duration/amount only as fallback.
    def _billing_cycles(self):
        created = 0
        for plan in Subscription.objects.all():
            if plan.billingCycles.exists():
                continue  # already correct (seeded v3 plans, or repaired)
            entries = plan.availableDuration if isinstance(plan.availableDuration, list) else []
            seen = set()
            for e in entries:
                if not isinstance(e, dict):
                    continue
                months, price = _months(e.get("duration")), _dec(e.get("price"))
                if months <= 0 or price is None or months in seen:
                    continue
                seen.add(months)
                PlanBillingCycle.objects.create(
                    plan=plan, durationMonths=months, price=price,
                    oldPrice=_dec(e.get("oldPrice")),
                    badgeLabel=str(e.get("badgeLabel") or "")[:100], isActive=True)
                created += 1
            if not seen:  # no usable JSON entries -> single cycle from scalars
                months, price = _months(plan.duration), _dec(plan.amount)
                if months > 0 and price is not None:
                    PlanBillingCycle.objects.create(
                        plan=plan, durationMonths=months, price=price, isActive=True)
                    created += 1
        self._log(f"billing cycles created: {created}")

    # gap 4 — v3 routes business detail by slug; old rows predate auto-slug.
    # Mirrors Business.save()'s slug logic, via .update() (no signals).
    def _business_slugs(self):
        fixed = 0
        for b in Business.objects.filter(Q(slug__isnull=True) | Q(slug="")):
            base = slugify(b.businessName) or "business"
            candidate, n = base, 1
            while Business.objects.filter(slug=candidate).exclude(pk=b.pk).exists():
                n += 1
                candidate = f"{base}-{n}"
            Business.objects.filter(pk=b.pk).update(slug=candidate)
            fixed += 1
        self._log(f"business slugs backfilled: {fixed}")

    # gap 5 — old frontend never sent isWorking, so every configured schedule
    # persisted False alongside real hours. Real hours = the business set that
    # day as working.
    def _day_schedules(self):
        n = (DaySchedule.objects.filter(isWorking=False)
             .exclude(startTime=F("endTime")).update(isWorking=True))
        self._log(f"day schedules marked working: {n}")

    # gap 12 — 0067 snapshotted durationMonths from the broken parser (always
    # 0 -> never set). Date delta is ground truth on every prod row.
    def _plan_duration_months(self):
        fixed = 0
        for Model in (BusinessPlan, ShopPlan, ArchitectPlan, AutomationPlan):
            for p in Model.objects.filter(durationMonths__isnull=True):
                months = 0
                if p.expireDate and p.lastActivate:
                    months = max(1, round((p.expireDate - p.lastActivate).days / 30))
                elif p.plan_id:
                    months = _months(p.plan.duration)
                if months > 0:
                    Model.objects.filter(pk=p.pk).update(durationMonths=months)
                    fixed += 1
        self._log(f"purchased-plan durationMonths backfilled: {fixed}")

    # gap 11 — completionPercent/canGoLive stale (nothing recomputes them).
    def _completion(self):
        self._log(f"completion recomputed for {recompute_all_completion()} entities")

    # gap 13 — v3 home hero reads HomeHeroBanner; prod hero imagery lives in
    # StockMedia(page=home, section=hero). Fill the seeded slides' empty
    # backgroundImageUrl in display order (prod wins on data).
    def _hero_images(self):
        stock = list(StockMedia.objects
                     .filter(page__name="home", section__name="hero")
                     .exclude(image__isnull=True).exclude(image="")
                     .order_by("index", "id"))
        banners = list(HomeHeroBanner.objects
                       .filter(page="home", backgroundImageUrl="")
                       .order_by("displayOrder", "id"))
        for banner, media in zip(banners, stock):
            HomeHeroBanner.objects.filter(pk=banner.pk).update(backgroundImageUrl=media.image)
        self._log(f"hero banner images backfilled: {min(len(banners), len(stock))}")

    # gap 9 — legacy AdAsset.meta {'link': <image url>} : 'link' is the image,
    # not a CTA. Remap so the ad renderer's buttonLink chain can't pick it up.
    def _ad_meta(self):
        fixed = 0
        for a in AdAsset.objects.all():
            meta = a.meta if isinstance(a.meta, dict) else {}
            link = meta.get("link")
            if isinstance(link, str) and _IMG_RE.search(link):
                meta.setdefault("imageUrl", link)
                del meta["link"]
                AdAsset.objects.filter(pk=a.pk).update(meta=meta)
                fixed += 1
        self._log(f"ad meta image links remapped: {fixed}")
