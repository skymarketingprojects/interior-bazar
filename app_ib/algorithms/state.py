"""Inline/stateful algorithms:
 21. Recently Viewed Eviction   record_recently_viewed()
 20. Notification Dedupe        notify()
     Saved item upsert          toggle_saved()
"""
from datetime import timedelta
from django.utils import timezone
from django.db import transaction

from app_ib.Utils.EngineConfig import ALGO
from app_ib.algorithms.helpers import content_type_for


# ---------------------------------------------------------------------------
# 21. Recently Viewed Eviction — cap 50, evict oldest inline at write time
# ---------------------------------------------------------------------------
@transaction.atomic
def record_recently_viewed(user, entity_type, object_id):
    from app_ib.models import RecentlyViewed
    ct = content_type_for(entity_type)
    obj, created = RecentlyViewed.objects.update_or_create(
        user=user, contentType=ct, objectId=object_id,
        defaults={"viewedAt": timezone.now()},
    )
    count = RecentlyViewed.objects.filter(user=user).count()
    cap = ALGO.RECENTLY_VIEWED_CAP
    if count > cap:
        evict = (RecentlyViewed.objects.filter(user=user)
                 .order_by("viewedAt")[:count - cap])
        RecentlyViewed.objects.filter(id__in=[e.id for e in evict]).delete()
    return obj


# ---------------------------------------------------------------------------
# 20. Notification Dedupe — collapse identical (type, dedupeKey) within 60 min
# ---------------------------------------------------------------------------
def notify(user, ntype, title, body="", action_url="", dedupe_key="", metadata=None):
    from app_ib.models import Notification
    now = timezone.now()
    window_start = now - timedelta(seconds=ALGO.NOTIFICATION_DEDUPE_WINDOW_SECONDS)

    existing = None
    if dedupe_key:
        existing = (Notification.objects.filter(
            user=user, type=ntype, dedupeKey=dedupe_key, timestamp__gte=window_start)
            .order_by("-timestamp").first())

    if existing:
        existing.groupCount += 1
        existing.timestamp = now
        existing.title = title or existing.title
        existing.body = body or existing.body
        existing.save(update_fields=["groupCount", "timestamp", "title", "body"])
        _publish_notification(existing)
        return existing

    notif = Notification.objects.create(
        user=user, type=ntype, title=title, body=body, actionUrl=action_url,
        dedupeKey=dedupe_key, metadata=metadata or {},
    )
    _publish_notification(notif)
    return notif


def _publish_notification(notif):
    from app_ib.Utils.sse_streamer import publish_notification
    publish_notification(notif.user_id, {
        "id": notif.id, "type": notif.type, "title": notif.title, "body": notif.body,
        "groupCount": notif.groupCount, "timestamp": notif.timestamp.isoformat(),
    })


# ---------------------------------------------------------------------------
# Saved item upsert (idempotent) + check
# ---------------------------------------------------------------------------
def toggle_saved(user, entity_type, object_id):
    from app_ib.models import SavedItem
    ct = content_type_for(entity_type)
    existing = SavedItem.objects.filter(user=user, contentType=ct, objectId=object_id).first()
    if existing:
        existing.delete()
        return False  # now unsaved
    SavedItem.objects.create(user=user, contentType=ct, objectId=object_id)
    return True       # now saved
