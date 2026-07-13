"""Re-verify recent gateway payments missed mid-flow — the nightly 02:00 cron.

A buyer can pay on Cashfree but drop before the return leg updates our row.
This re-checks every recent non-PAID gateway transaction against Cashfree via
the existing PaymentGatewayController.CheckPaymentStatus (which also activates
the purchased plan/ad on PAID). Manual (UPI/NEFT proof) rows are excluded —
those are verified by an admin, not the gateway.
"""
from datetime import timedelta

from asgiref.sync import async_to_sync
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Re-verify recent pending gateway payments against Cashfree and activate missed services."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=4, help="How many days back to re-check (default 4).")

    def handle(self, *args, **options):
        from app_ib.models import TransectionData
        from app_ib.Utils.Names import NAMES
        from app_ib.Controllers.PaymentGateway.PaymentGatewayController import PaymentGatewayController

        since = timezone.now() - timedelta(days=options["days"])
        pending = (
            TransectionData.objects
            .filter(createdAt__gte=since, paymentMethod="gateway")
            .exclude(orderStatus=NAMES.CF_PAID)
        )

        total = pending.count()
        verified = failed = 0
        for txn in pending.iterator():
            try:
                async_to_sync(PaymentGatewayController.CheckPaymentStatus)(txn.transactionId, {})
                verified += 1
            except Exception as exc:
                failed += 1
                self.stderr.write(f"[fail] {txn.transactionId}: {exc}")

        self.stdout.write(self.style.SUCCESS(
            f"verify_pending_payments done — checked {verified}/{total} pending txns ({failed} errors)"
        ))
