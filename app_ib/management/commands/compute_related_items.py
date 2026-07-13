"""Recompute co-view RelatedItem pairs — the nightly 03:30 cron.

Sessions that viewed entity A and entity B produce a co-view pair; the pair's
score is its co-occurrence count across sessions. Top pairs per source replace
the stored RelatedItem rows (the /engine/related/ endpoint serves these first,
falling back to same-category/trending when rows are missing). Safe and a
no-op on an empty DB.

ponytail: whole-table recompute in memory over a 30-day window; move to
incremental/SQL aggregation only if ViewEvent volume ever makes this slow.
"""
from collections import Counter, defaultdict
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

WINDOW_DAYS = 30
TOP_PER_SOURCE = 12
MAX_ENTITIES_PER_SESSION = 30  # a crawler session must not explode the pair count


class Command(BaseCommand):
    help = "Recompute co-view RelatedItem pairs from the last 30 days of ViewEvents."

    def handle(self, *args, **options):
        from app_ib.engine_models import ViewEvent, RelatedItem

        since = timezone.now() - timedelta(days=WINDOW_DAYS)

        # sessionId → ordered set of (contentType_id, objectId)
        sessions = defaultdict(list)
        events = (
            ViewEvent.objects
            .filter(timestamp__gte=since)
            .exclude(sessionId="")
            .values_list("sessionId", "contentType_id", "objectId")
        )
        for sid, ct_id, oid in events.iterator():
            ents = sessions[sid]
            key = (ct_id, oid)
            if key not in ents and len(ents) < MAX_ENTITIES_PER_SESSION:
                ents.append(key)

        # co-occurrence counts, directional (source → target)
        pair_counts = Counter()
        for ents in sessions.values():
            for a in ents:
                for b in ents:
                    if a != b:
                        pair_counts[(a, b)] += 1

        # keep top N per source
        by_source = defaultdict(list)
        for (src, tgt), count in pair_counts.items():
            by_source[src].append((count, tgt))

        rows = []
        for src, targets in by_source.items():
            targets.sort(reverse=True)
            for count, tgt in targets[:TOP_PER_SOURCE]:
                rows.append(RelatedItem(
                    sourceContentType_id=src[0], sourceObjectId=src[1],
                    targetContentType_id=tgt[0], targetObjectId=tgt[1],
                    score=float(count), reason="co_view",
                ))

        # full replace — the table is a derived cache
        RelatedItem.objects.all().delete()
        if rows:
            RelatedItem.objects.bulk_create(rows, batch_size=500)

        self.stdout.write(self.style.SUCCESS(
            f"compute_related_items done - {len(sessions)} sessions -> {len(rows)} pairs stored"
        ))
