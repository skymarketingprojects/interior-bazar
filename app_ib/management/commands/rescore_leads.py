"""Re-score & re-tier every LeadQuery with the CURRENT qualification weights.

Scoring is creation-only by design (tuning weights only affects new leads), so
historical leads keep their score until this command is run manually. Not a cron,
not a live re-score — an explicit admin action after changing weights (task 33).

    python manage.py rescore_leads          # apply
    python manage.py rescore_leads --dry-run # report changes without writing
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Re-score & re-tier all LeadQuery rows using the current qualification weights."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true",
                            help="Report how many leads would change without saving.")

    def handle(self, *args, **options):
        from app_ib.models import LeadQuery
        from app_ib.Controllers.Query.Tasks.QueryTasks import compute_score_and_tier
        from interior_admin.models import QualificationWeightConfig
        from interior_admin.Controllers.Weights.WeightsController import merged_weights

        cfg, _ = QualificationWeightConfig.objects.get_or_create(id=1)
        weights = merged_weights(cfg.weights)
        dry = options.get("dry_run")

        changed = total = 0
        for lead in LeadQuery.objects.all().iterator():
            total += 1
            score, tier = compute_score_and_tier(lead, weights)
            if lead.score == score and lead.tier == tier:
                continue
            changed += 1
            if not dry:
                lead.score = score
                lead.tier = tier
                lead.save(update_fields=["score", "tier"])

        verb = "would change" if dry else "updated"
        self.stdout.write(self.style.SUCCESS(
            f"rescore_leads done - {changed}/{total} leads {verb}"
        ))
