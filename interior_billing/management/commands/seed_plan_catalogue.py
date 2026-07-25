"""
Replaces the plan catalogue with the canonical 12 plans from
interior_billing/data/plan_catalogue.json (extracted from the prototype's
plans-checkout page; tags come from its own selectPlan(name, tag) calls).

Why a replace and not an upsert: the live catalogue still used the RETIRED names
(Signature / Elite / Enterprise, which ib-plans.js says must never be shown) plus
one-row-per-cycle duplicates and test rows, and dev/stage had already drifted apart
(18 plans/11 cycles vs 17/21). There is no stable key to upsert against.

Existing rows are SOFT-deleted (isActive=False, is_delete=True), never dropped:
eight FKs point at Subscription (BusinessPlan / ShopPlan / ArchitectPlan /
AutomationPlan / TransectionData / ...) with on_delete=SET_NULL, so a hard delete
would silently orphan purchase history. --hard-delete forces a real delete for a
throwaway env.

Prices in PlanBillingCycle.price are GST-INCLUSIVE, matching the engine serializer
(_plan_cycles emits total == price with gstLine "incl. GST").
"""
import json
from pathlib import Path

from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db import transaction

from interior_billing.models import PlanBillingCycle, Subscription

DATA = Path(__file__).resolve().parent.parent.parent / "data" / "plan_catalogue.json"


class Command(BaseCommand):
    help = "Replace the plan catalogue with the canonical plans from plan_catalogue.json."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true",
                            help="Report what would change without writing.")
        parser.add_argument("--hard-delete", action="store_true",
                            help="Really DELETE old rows instead of soft-deleting them. "
                                 "Orphans any purchased-plan FKs (SET_NULL).")

    def handle(self, *args, **opts):
        catalogue = json.loads(DATA.read_text(encoding="utf-8"))["plans"]
        dry, hard = opts["dry_run"], opts["hard_delete"]
        keep = {p["tag"] for p in catalogue}

        old = list(Subscription.objects.exclude(tag__in=keep))
        self.stdout.write(
            f"{'would ' if dry else ''}{'delete' if hard else 'archive'} {len(old)} existing plan(s):"
        )
        for s in old:
            self.stdout.write(f"    [{s.id}] {s.planFamily}/{s.title} tag={s.tag!r}")

        if dry:
            for p in catalogue:
                cy = " ".join(f"{c['durationMonths']}mo=Rs{c['price']}" for c in p["cycles"])
                self.stdout.write(f"  would seed {p['tag']:20} {p['title']:22} {cy}")
            self.stdout.write(self.style.WARNING("dry run — nothing written"))
            return

        with transaction.atomic():
            if hard:
                PlanBillingCycle.objects.filter(plan__in=old).delete()
                Subscription.objects.filter(pk__in=[s.pk for s in old]).delete()
            else:
                # Archived rows stay resolvable for existing purchases but leave the
                # public catalogue, which filters isActive=True, is_delete=False.
                Subscription.objects.filter(pk__in=[s.pk for s in old]).update(
                    isActive=False, is_delete=True
                )

            for p in catalogue:
                plan, _ = Subscription.objects.update_or_create(
                    tag=p["tag"],
                    defaults={
                        "title": p["title"],
                        "planFamily": p["planFamily"],
                        "entityType": p["entityType"],
                        "tier": p["tier"],
                        "amount": p["amount"],
                        "payableAmount": p["payableAmount"],
                        "services": p["services"],
                        "features": p["features"],
                        "badge": p["badge"],
                        "badgeIcon": p["badgeIcon"],
                        "cardContent": p["cardContent"],
                        "duration": "12",
                        "isActive": True,
                        "is_delete": False,
                    },
                )
                # Cycles are the money source of truth — rewrite them wholesale so a
                # removed duration cannot linger and stay purchasable.
                plan.billingCycles.all().delete()
                for c in p["cycles"]:
                    PlanBillingCycle.objects.create(
                        plan=plan,
                        durationMonths=c["durationMonths"],
                        price=c["price"],
                        badgeLabel=c.get("badgeLabel", ""),
                        isActive=True,
                    )
                cy = " ".join(f"{c['durationMonths']}mo=Rs{c['price']}" for c in p["cycles"])
                self.stdout.write(f"  seeded {p['tag']:20} {p['title']:22} {cy}")

        # GetSubscription caches the whole catalogue for 24h under this key; without
        # this the API keeps serving the old plans. See the legal-pages double-cache.
        cache.delete("subscription_plans_list")

        self.stdout.write(self.style.SUCCESS(
            f"{len(catalogue)} plans seeded, {len(old)} {'deleted' if hard else 'archived'}, "
            "catalogue cache cleared"
        ))
