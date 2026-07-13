"""Discovery/trending engine background jobs — the */15min cron entrypoint.

Wires the existing plain functions in app_ib.algorithms into the crontab's
`python manage.py run_engine_jobs` (the command referenced by `crontab` and
`background.py` but never created). Each job is independent and idempotent;
one failing must not stop the rest. Safe on an empty DB (each job just
computes/caches empty boards).
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run discovery-engine background jobs (ratings, analytics, trending, discovery lists, synthetic feed)."

    def handle(self, *args, **options):
        from app_ib.algorithms import aggregation
        from app_ib.algorithms.feed import generate_synthetic_feed_events

        jobs = [
            ("recompute_ratings", aggregation.recompute_ratings),
            ("aggregate_daily_analytics", aggregation.aggregate_daily_analytics),
            ("compute_avg_response", aggregation.compute_avg_response),
            ("calculate_trending_searches", aggregation.calculate_trending_searches),
            ("compute_city_pulse", aggregation.compute_city_pulse),
            ("compute_daily_discovery_lists", aggregation.compute_daily_discovery_lists),
            ("compute_fresh_catalogues", aggregation.compute_fresh_catalogues),
            ("generate_synthetic_feed_events", generate_synthetic_feed_events),
        ]

        failed = 0
        for name, fn in jobs:
            try:
                fn()
                self.stdout.write(self.style.SUCCESS(f"[ok] {name}"))
            except Exception as exc:  # one job failing must not stop the rest
                failed += 1
                self.stderr.write(f"[fail] {name}: {exc}")

        self.stdout.write(f"run_engine_jobs done — {len(jobs) - failed}/{len(jobs)} succeeded")
