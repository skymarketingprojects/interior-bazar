"""Algorithm 19 — Genuine View Dedup. A shared filter (not a job) called by the
leaderboard (3) and discovery (12) jobs. Removes null-session, duplicate,
self, and low-dwell views from a ViewEvent queryset.

Returns a list of "genuine" ViewEvent ids (deduped to 1 per (user|session) per
entity per 24h window).
"""
from app_ib.Utils.EngineConfig import ALGO


def genuine_view_event_ids(view_qs, owner_user_id_by_object=None):
    """
    view_qs: a ViewEvent queryset already scoped to the desired time window.
    owner_user_id_by_object: optional dict {(contentType_id, objectId): owner_user_id}
        used for self-view exclusion. If a view's user is the entity owner it is dropped.

    Filter order (per spec):
      1. null-session exclusion (no user AND no sessionId)
      2. self-view exclusion
      3. dwell threshold: dwellSeconds >= 2 OR dwellSeconds IS NULL
      4. dedup: <=1 view per (user|session) per entity per 24h window
    """
    owner_map = owner_user_id_by_object or {}
    min_dwell = ALGO.GENUINE_VIEW_MIN_DWELL_SECONDS

    seen = {}   # (entity_key, identity, bucket) -> event_id   (first wins)
    window_seconds = ALGO.GENUINE_VIEW_DEDUP_WINDOW_HOURS * 3600

    fields = view_qs.values(
        "id", "user_id", "sessionId", "contentType_id", "objectId",
        "dwellSeconds", "timestamp",
    ).order_by("timestamp")

    keep = []
    for v in fields:
        # 1. null-session exclusion
        if not v["user_id"] and not v["sessionId"]:
            continue
        entity_key = (v["contentType_id"], v["objectId"])
        # 2. self-view exclusion
        owner = owner_map.get(entity_key)
        if owner and v["user_id"] == owner:
            continue
        # 3. dwell threshold (null passes)
        dwell = v["dwellSeconds"]
        if dwell is not None and dwell < min_dwell:
            continue
        # 4. dedup per (identity, entity, 24h bucket)
        identity = ("u", v["user_id"]) if v["user_id"] else ("s", v["sessionId"])
        bucket = int(v["timestamp"].timestamp() // window_seconds)
        dedupe_key = (entity_key, identity, bucket)
        if dedupe_key in seen:
            continue
        seen[dedupe_key] = v["id"]
        keep.append(v["id"])
    return keep
