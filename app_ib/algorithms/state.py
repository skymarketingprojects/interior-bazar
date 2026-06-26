"""Inline/stateful algorithms:
 21. Recently Viewed Eviction   record_recently_viewed()
 20. Notification Dedupe        notify()
     Saved item upsert          toggle_saved()
"""
from datetime import timedelta
from django.utils import timezone
from django.db import transaction

from app_ib.Utils.EngineConfig import ALGO, ENGAGEMENT_VERB
from app_ib.algorithms.helpers import content_type_for, get_model, owner_user_id


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
    # Inbound engagement: tell the entity owner "someone saved your <entity>".
    try:
        record_engagement(ENGAGEMENT_VERB.SAVE, entity_type, object_id, actor=user)
    except Exception:
        pass  # fire-and-forget — never let the feed write break the save
    return True       # now saved


# ---------------------------------------------------------------------------
# Inbound-engagement feed writer (EngagementActivity)
#   Records ONE row per action ANOTHER user took on an entity the seller owns
#   ("someone viewed/saved/enquired about your <entity>"). Keyed by `owner` so
#   the dashboard feed is a single indexed filter(owner=...). Self-actions
#   (actor == owner) are skipped; repeats within DEDUPE_MINUTES bump count.
#   Callers MUST treat this as fire-and-forget (wrap in try/except).
# ---------------------------------------------------------------------------
def record_engagement(verb, entity_type, object_id, actor=None, actor_name=""):
    from app_ib.engine_models import EngagementActivity

    model = get_model(entity_type)
    obj = model.objects.filter(id=object_id).first()
    if obj is None:
        return None
    owner_id = owner_user_id(obj)
    if not owner_id:
        return None  # ownerless entity — nobody to notify

    actor_id = getattr(actor, "id", None) if getattr(actor, "is_authenticated", False) else None
    if actor_id and actor_id == owner_id:
        return None  # don't surface a seller's own actions on their own entity

    ct = content_type_for(entity_type)
    name = (getattr(obj, "businessName", None) or getattr(obj, "name", None)
            or getattr(obj, "title", None) or "")
    display_actor = actor_name or ENGAGEMENT_VERB.ANON_ACTOR

    now = timezone.now()
    window_start = now - timedelta(minutes=ENGAGEMENT_VERB.DEDUPE_MINUTES)
    existing = (EngagementActivity.objects
                .filter(owner_id=owner_id, contentType=ct, objectId=object_id,
                        verb=verb, actor_id=actor_id, timestamp__gte=window_start)
                .order_by("-timestamp").first())
    if existing is not None:
        existing.count = (existing.count or 1) + 1
        existing.timestamp = now
        existing.isRead = False
        if name:
            existing.entityName = name
        if actor_name:
            existing.actorName = actor_name
        existing.save(update_fields=["count", "timestamp", "isRead", "entityName", "actorName"])
        return existing.id

    row = EngagementActivity.objects.create(
        owner_id=owner_id, actor_id=actor_id, actorName=display_actor, verb=verb,
        contentType=ct, objectId=object_id, entityType=entity_type,
        entityName=name, timestamp=now)
    return row.id
