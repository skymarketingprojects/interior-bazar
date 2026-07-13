"""Collapse row-per-cycle Subscription plans into one canonical row + PlanBillingCycle
children, snapshot durationMonths onto purchased-plan rows, then soft-delete the siblings.

See task 30: money source of truth moves from `amount`/`availableDuration` JSON to the
PlanBillingCycle child model. Legacy fields stay for old rows (never re-written)."""
import re
from decimal import Decimal, InvalidOperation

from django.db import migrations


def _months(dur):
    """Old Subscription.duration -> months. >= 28 is treated as days (legacy), else months."""
    try:
        n = int(float(str(dur or "0").strip() or 0))
    except (ValueError, TypeError):
        return 0
    if n >= 28:  # days -> months
        return {90: 3, 180: 6, 365: 12, 730: 24}.get(n, max(1, round(n / 30)))
    return n


def _dec(val):
    """'₹84,999' / '29499' -> Decimal; None/blank/garbage -> None."""
    s = re.sub(r"[^\d.]", "", str(val or ""))
    if not s:
        return None
    try:
        d = Decimal(s)
    except InvalidOperation:
        return None
    return d if d > 0 else None


def forwards(apps, schema_editor):
    Subscription = apps.get_model("app_ib", "Subscription")
    Cycle = apps.get_model("app_ib", "PlanBillingCycle")
    purchase_models = [apps.get_model("app_ib", m) for m in
                       ("BusinessPlan", "ShopPlan", "ArchitectPlan", "AutomationPlan")]

    # Months for EVERY plan (incl. already-soft-deleted) so purchases on a pre-deleted
    # plan still get a durationMonths snapshot for expiry math.
    all_months = {s.id: _months(s.duration) for s in Subscription.objects.all()}

    rows = list(Subscription.objects.filter(is_delete=False).order_by("id"))

    # Group by (tag, planFamily) only when tag is non-empty; tagless legacy rows are
    # each their own plan (never collapse unrelated demo rows into one).
    groups = {}
    for s in rows:
        tag = (s.tag or "").strip()
        key = (tag, s.planFamily) if tag else (f"__id{s.id}", s.planFamily)
        groups.setdefault(key, []).append(s)

    # old plan id -> canonical plan id (for FK repoint); old plan id -> months (snapshot)
    canonical_of = {}
    months_of = {}

    for members in groups.values():
        members.sort(key=lambda s: s.id)
        canonical = members[0]
        seen_months = set()
        for s in members:
            m = _months(s.duration)
            months_of[s.id] = m
            canonical_of[s.id] = canonical.id
            price = _dec(s.amount)
            if m <= 0 or price is None or m in seen_months:
                continue  # unpriced/legacy or duplicate cycle -> no child row
            seen_months.add(m)
            curated = (s.availableDuration or [{}])
            curated = curated[0] if isinstance(curated, list) and curated else {}
            curated = curated if isinstance(curated, dict) else {}
            Cycle.objects.create(
                plan_id=canonical.id,
                durationMonths=m,
                price=price,
                oldPrice=_dec(curated.get("oldPrice")),
                badgeLabel=(curated.get("badgeLabel") or "")[:100],
                isActive=True,
            )
        # soft-delete siblings (keep canonical live)
        for s in members[1:]:
            s.is_delete = True
            s.save(update_fields=["is_delete"])

    # Snapshot durationMonths onto every purchased row, then repoint sibling FKs to canonical.
    for Model in purchase_models:
        for p in Model.objects.filter(plan__isnull=False).iterator():
            m = months_of.get(p.plan_id) or all_months.get(p.plan_id)
            if m:
                p.durationMonths = m
            new_plan = canonical_of.get(p.plan_id)
            if new_plan and new_plan != p.plan_id:
                p.plan_id = new_plan
            p.save(update_fields=["durationMonths", "plan"])


class Migration(migrations.Migration):
    dependencies = [("app_ib", "0066_architectplan_durationmonths_and_more")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
