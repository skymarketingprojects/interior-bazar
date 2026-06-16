"""
Scoring algorithms (background jobs):
  1. Trending Score      compute_trending_scores()
  2. Hot Score           compute_hot_scores()
  3. Leaderboard         compute_leaderboards()
  4. Behind the Trend    compute_behind_the_trend()
 15. Cached Labels       compute_cached_labels()

All writes are idempotent (upsert / overwrite). Catelogue "download" signal is
omitted (no DownloadEvent in the schema yet) — noted inline.
"""

import math
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Max

from app_ib.Utils.EngineConfig import (
    ENTITY_TYPE, TRENDING_PERIOD, LEADERBOARD_PERIOD, LEADERBOARD_BOARD,
    LEADERBOARD_SCOPE, CLICK_TYPE, PLAN_TIER, LABEL, ALGO,
)
from app_ib.models import ViewEvent, ClickEvent, SavedItem, TrendingScore

from app_ib.algorithms.helpers import (
    get_model, content_type_for, owner_user_id, entity_city,
)
from app_ib.algorithms.genuine_view import genuine_view_event_ids


# ---------------------------------------------------------------------------
# Leads helper — map an entity type's lead counts within a window
# ---------------------------------------------------------------------------
def _lead_counts(entity_type, cutoff):
    from app_ib.models import LeadQuery
    field = {
        ENTITY_TYPE.BUSINESS: "business_id",
        ENTITY_TYPE.PRODUCT: "product_id",
        ENTITY_TYPE.SERVICE: "service_id",
        ENTITY_TYPE.CATELOGUE: "catalouge_id",
    }.get(entity_type) 
    if not field:
        return {}, {}
    qs = LeadQuery.objects.filter(**{f"{field}__isnull": False})
    if cutoff:
        qs = qs.filter(timestamp__gte=cutoff)
    counts, last = {}, {}
    for row in qs.values(field).annotate(c=Count("id"), m=Max("timestamp")):
        counts[row[field]] = row["c"]
        last[row[field]] = row["m"]
    return counts, last


# ---------------------------------------------------------------------------
# 1. Trending Score
# ---------------------------------------------------------------------------

def compute_trending_scores():
    now = timezone.now()
    written = 0

    for entity_type in ENTITY_TYPE.SCORED:
        model = get_model(entity_type)
        ct = content_type_for(entity_type)
        # daily field value caches the daily national score
        daily_national = {}

        for period in TRENDING_PERIOD.ALL:
            weights = ALGO.TRENDING_WEIGHTS[period]
            cutoff = now - timedelta(hours=ALGO.TRENDING_WINDOW_HOURS[period])

            # aggregate per (objectId, city)
            agg = {}        # (objId, city) -> weighted sum
            national = {}   # objId -> weighted sum
            last_seen = {}  # objId -> latest interaction datetime

            def add(obj_id, city, signal, n, latest):
                w = weights[signal] * n
                # city-dimension bucket (only when a real city is present)
                if city:
                    agg[(obj_id, city)] = agg.get((obj_id, city), 0.0) + w
                # national bucket always gets the weight exactly once
                agg[(obj_id, "")] = agg.get((obj_id, ""), 0.0) + w
                national[obj_id] = national.get(obj_id, 0.0) + w
                if latest and (obj_id not in last_seen or latest > last_seen[obj_id]):
                    last_seen[obj_id] = latest

            for row in (ViewEvent.objects.filter(contentType=ct, timestamp__gte=cutoff)
                        .values("objectId", "city").annotate(c=Count("id"), m=Max("timestamp"))):
                add(row["objectId"], row["city"] or "", "view", row["c"], row["m"])
            for row in (ClickEvent.objects.filter(contentType=ct, timestamp__gte=cutoff)
                        .values("objectId").annotate(c=Count("id"), m=Max("timestamp"))):
                # ClickEvent has no city column in this schema -> national only
                add(row["objectId"], "", "click", row["c"], row["m"])
            for row in (SavedItem.objects.filter(contentType=ct, timestamp__gte=cutoff)
                        .values("objectId").annotate(c=Count("id"), m=Max("timestamp"))):
                add(row["objectId"], "", "save", row["c"], row["m"])

            lead_counts, lead_last = _lead_counts(entity_type, cutoff)
            for obj_id, c in lead_counts.items():
                add(obj_id, "", "lead", c, lead_last.get(obj_id))

            # apply recency decay + upsert TrendingScore rows
            for (obj_id, city), raw in agg.items():
                last = last_seen.get(obj_id)
                hours = ((now - last).total_seconds() / 3600.0) if last else 0.0
                score = raw * math.exp(-ALGO.TRENDING_DECAY_LAMBDA * hours)
                TrendingScore.objects.update_or_create(
                    contentType=ct, objectId=obj_id, period=period, city=city,
                    defaults={"score": round(score, 4)},
                )
                written += 1
                if city == "" and period == TRENDING_PERIOD.DAILY:
                    daily_national[obj_id] = round(score, 4)

        # write entity.trendingScore = daily national score; zero out the rest
        for obj in model.objects.all().only("id", "trendingScore"):
            obj.trendingScore = daily_national.get(obj.id, 0.0)
            obj.save(update_fields=["trendingScore"])

        # assign per (period, city) ranks
        _rank_trending(content_type_for(entity_type))

    return written


def _rank_trending(ct):
    from app_ib.models import TrendingScore
    groups = (TrendingScore.objects.filter(contentType=ct)
              .values_list("period", "city").distinct())
    for period, city in groups:
        rows = list(TrendingScore.objects.filter(contentType=ct, period=period, city=city)
                    .order_by("-score", "objectId"))
        for i, r in enumerate(rows, start=1):
            if r.rank != i:
                r.rank = i
                r.save(update_fields=["rank"])


# ---------------------------------------------------------------------------
# 2. Hot Score
# ---------------------------------------------------------------------------
def compute_hot_scores():
    from app_ib.models import ViewEvent
    now = timezone.now()
    c1 = now - timedelta(hours=1)
    c6 = now - timedelta(hours=6)
    c24 = now - timedelta(hours=24)
    w = ALGO.HOT_WEIGHTS
    updated = 0

    for entity_type in ENTITY_TYPE.SCORED:
        model = get_model(entity_type)
        ct = content_type_for(entity_type)
        lead_counts, _ = _lead_counts(entity_type, c24)

        def real_views(cutoff):
            # exclude null-session bots (no user and no session)
            qs = ViewEvent.objects.filter(contentType=ct, timestamp__gte=cutoff).exclude(
                user__isnull=True, sessionId="")
            counts = {}
            for row in qs.values("objectId").annotate(c=Count("id")):
                counts[row["objectId"]] = row["c"]
            return counts

        v1, v6 = real_views(c1), real_views(c6)
        # owner self-views excluded: subtract owner views per entity
        for obj in model.objects.all():
            owner = owner_user_id(obj)
            own1 = own6 = 0
            if owner:
                own1 = ViewEvent.objects.filter(contentType=ct, objectId=obj.id,
                                                timestamp__gte=c1, user_id=owner).count()
                own6 = ViewEvent.objects.filter(contentType=ct, objectId=obj.id,
                                                timestamp__gte=c6, user_id=owner).count()
            views1 = max(0, v1.get(obj.id, 0) - own1)
            views6 = max(0, v6.get(obj.id, 0) - own6)
            leads24 = lead_counts.get(obj.id, 0)
            obj.hotScore = round(views1 * w["views_1h"] + views6 * w["views_6h"]
                                 + leads24 * w["leads_24h"], 4)
            obj.save(update_fields=["hotScore"])
            updated += 1
    return updated


# ---------------------------------------------------------------------------
# 3. Leaderboard Engagement
# ---------------------------------------------------------------------------
def _entity_display(entity_type, obj):
    name = (getattr(obj, "businessName", None) or getattr(obj, "name", None)
            or getattr(obj, "title", None) or str(obj))
    image = (getattr(obj, "coverImageUrl", None) or getattr(obj, "coverImage", None)
             or getattr(obj, "catelougeImage", None) or "")
    slug = getattr(obj, "slug", "") or ""
    return name, image or "", slug


def compute_leaderboards():
    from app_ib.models import ViewEvent, ClickEvent, LeaderboardEntry
    now = timezone.now()
    weights = ALGO.LEADERBOARD_WEIGHTS
    written = 0

    for period in LEADERBOARD_PERIOD.ALL:
        days = ALGO.LEADERBOARD_PERIOD_DAYS[period]
        cutoff = now - timedelta(days=days) if days else None

        scored = []   # list of dicts across all entity types (combined board)
        for entity_type in ENTITY_TYPE.SCORED:
            model = get_model(entity_type)
            ct = content_type_for(entity_type)

            # owner map for self-view exclusion
            owner_map = {}
            objs = {o.id: o for o in model.objects.all()}
            for oid, o in objs.items():
                owner_map[(ct.id, oid)] = owner_user_id(o)

            view_qs = ViewEvent.objects.filter(contentType=ct)
            if cutoff:
                view_qs = view_qs.filter(timestamp__gte=cutoff)
            genuine_ids = genuine_view_event_ids(view_qs, owner_map)
            gv_by_obj = {}
            for row in (ViewEvent.objects.filter(id__in=genuine_ids)
                        .values("objectId").annotate(c=Count("id"))):
                gv_by_obj[row["objectId"]] = row["c"]

            click_qs = ClickEvent.objects.filter(contentType=ct, clickType__in=CLICK_TYPE.ENGAGEMENT)
            if cutoff:
                click_qs = click_qs.filter(timestamp__gte=cutoff)
            clicks_by_obj = {}
            for row in click_qs.values("objectId").annotate(c=Count("id")):
                clicks_by_obj[row["objectId"]] = row["c"]

            for oid, o in objs.items():
                gv = gv_by_obj.get(oid, 0)
                clk = clicks_by_obj.get(oid, 0)
                score = gv * weights["genuine_views"] + clk * weights["clicks"]
                if score <= 0:
                    continue
                name, image, slug = _entity_display(entity_type, o)
                scored.append({
                    "ct": ct, "entity_type": entity_type, "obj": o,
                    "score": score, "gv": gv, "clk": clk,
                    "name": name, "image": image, "slug": slug,
                })

        # combined board
        scored.sort(key=lambda d: d["score"], reverse=True)
        written += _write_leaderboard(LEADERBOARD_BOARD.COMBINED, period,
                                      LEADERBOARD_SCOPE.GLOBAL, scored)
        # per-category board (business only)
        biz_only = [d for d in scored if d["entity_type"] == ENTITY_TYPE.BUSINESS]
        written += _write_leaderboard(LEADERBOARD_BOARD.PER_CATEGORY, period,
                                      LEADERBOARD_SCOPE.CATEGORY, biz_only)
    return written


def _write_leaderboard(board_type, period, scope, scored):
    from app_ib.models import LeaderboardEntry
    written = 0
    top = scored[:ALGO.LEADERBOARD_PERSIST_TOP]
    keep_keys = set()
    for rank, d in enumerate(top, start=1):
        entry, _ = LeaderboardEntry.objects.update_or_create(
            boardType=board_type, period=period, scope=scope,
            contentType=d["ct"], objectId=d["obj"].id,
            defaults={
                "entityType": d["entity_type"], "displayName": d["name"][:255],
                "imageUrl": d["image"], "slug": (d["slug"] or "")[:255],
                "rank": rank, "score": round(d["score"], 4),
                "genuineViews": d["gv"], "clicks": d["clk"],
            },
        )
        keep_keys.add((d["ct"].id, d["obj"].id))
        written += 1
    # drop stale rows for this board that fell out of the top list
    for e in LeaderboardEntry.objects.filter(boardType=board_type, period=period, scope=scope):
        if (e.contentType_id, e.objectId) not in keep_keys:
            e.delete()
    return written


# ---------------------------------------------------------------------------
# 4. Behind the Trend (template copy fallback; Gemini deferred)
# ---------------------------------------------------------------------------
def _plan_tier(business):
    plan = business.business_plan.filter(isActive=True).select_related("plan").first() \
        if hasattr(business, "business_plan") else None
    title = (getattr(getattr(plan, "plan", None), "title", "") or "").lower()
    for tier in (PLAN_TIER.PREMIUM, PLAN_TIER.PRO, PLAN_TIER.BASIC):
        if tier in title:
            return tier
    return PLAN_TIER.FREE


def compute_behind_the_trend():
    from app_ib.models import Business, LeaderboardEntry, BehindTheTrendStory, BusinessAnalytics
    from app_ib.algorithms.helpers import content_type_for
    today = timezone.now().date()
    ct = content_type_for(ENTITY_TYPE.BUSINESS)
    bw = ALGO.BEHIND_TREND_WEIGHTS

    lb = {e.objectId: e for e in LeaderboardEntry.objects.filter(
        boardType=LEADERBOARD_BOARD.COMBINED, period=LEADERBOARD_PERIOD.WEEKLY)}

    selected = []
    for biz in Business.objects.all():
        lb_entry = lb.get(biz.id)
        lb_score = lb_entry.score if lb_entry else 0.0
        tr_score = biz.trendingScore or 0.0
        mult = ALGO.BEHIND_TREND_PLAN_MULTIPLIER[_plan_tier(biz)]
        sel = (lb_score * bw["leaderboard"] + tr_score * bw["trending"]) * mult
        if sel <= 0:
            continue
        selected.append((sel, biz, lb_entry))
    selected.sort(key=lambda t: t[0], reverse=True)

    created = 0
    for rank, (sel, biz, lb_entry) in enumerate(selected[:ALGO.BEHIND_TREND_TOP_N], start=1):
        existing = BehindTheTrendStory.objects.filter(business=biz, snapshotDate=today).first()
        if existing and existing.isAiEdited:
            continue
        # enquiry growth from analytics (if present)
        growth = (BusinessAnalytics.objects.filter(contentType=ct, objectId=biz.id)
                  .order_by("-date").values_list("enquiryGrowthPct", flat=True).first())
        rank_to = lb_entry.rank if lb_entry else rank
        window_label = "last 7 days"
        # AI copy (Gemini temp 0.8) with deterministic template fallback
        from app_ib.algorithms.ai import generate_trend_story
        copy = generate_trend_story(biz.businessName, rank_to, window_label, growth)
        BehindTheTrendStory.objects.update_or_create(
            business=biz, snapshotDate=today,
            defaults={
                "rank": rank, "rankFrom": None, "rankTo": rank_to,
                "windowLabel": window_label,
                "planAtCompute": _plan_tier(biz),
                "imageUrl": biz.coverImageUrl or "",
                "enquiryGrowthPct": growth,
                "headline": copy["headline"],
                "eyebrow": copy["eyebrow"],
                "storyTitle": copy["storyTitle"],
                "storyBody": copy["storyBody"],
                "trendTags": copy["trendTags"],
                "isPublished": True,
            },
        )
        created += 1
    return created


# ---------------------------------------------------------------------------
# Editors Pick (Explore) — trending architects + Gemini editorial copy
# ---------------------------------------------------------------------------
def compute_editors_pick(top_n=5):
    from app_ib.models import Architect, EditorsPick
    from app_ib.algorithms.ai import generate_architect_editorial
    today = timezone.now().date()
    architects = list(Architect.objects.filter(isActive=True).order_by("-trendingScore")[:top_n])
    created = 0
    for rank, arch in enumerate(architects, start=1):
        existing = EditorsPick.objects.filter(architect=arch, snapshotDate=today).first()
        if existing and existing.isAiEdited:
            continue
        copy = generate_architect_editorial(arch.name, arch.city, arch.state, arch.rating)
        EditorsPick.objects.update_or_create(
            architect=arch, snapshotDate=today,
            defaults={"rank": rank, "eyebrow": copy["eyebrow"], "headline": copy["headline"],
                      "body": copy["body"], "trendTags": copy["trendTags"],
                      "imageUrl": arch.coverImage or "", "source": copy["source"],
                      "isPublished": True},
        )
        created += 1
    return created


# ---------------------------------------------------------------------------
# 15. Cached Labels (relative-rank method)
# ---------------------------------------------------------------------------
def compute_cached_labels():
    from django.db.models import F
    now = timezone.now()
    new_cutoff = now - timedelta(days=14)
    labelled = 0

    for entity_type in ENTITY_TYPE.SCORED:
        model = get_model(entity_type)
        objs = list(model.objects.all())
        if not objs:
            continue
        n = len(objs)
        top_n = max(1, int(math.ceil(n * 0.2)))   # top 20%

        trending_ids = {o.id for o in sorted(objs, key=lambda o: o.trendingScore or 0,
                                             reverse=True)[:top_n] if (o.trendingScore or 0) > 0}
        bestseller_ids = {o.id for o in sorted(objs, key=lambda o: getattr(o, "viewCount", 0) or 0,
                                              reverse=True)[:top_n] if getattr(o, "viewCount", 0)}

        created_field = "timestamp" if hasattr(model, "timestamp") else (
            "createdAt" if hasattr(objs[0], "createdAt") else None)

        for o in objs:
            label = LABEL.NONE
            if o.id in trending_ids:
                label = LABEL.TRENDING
            elif o.id in bestseller_ids:
                label = LABEL.BESTSELLER
            else:
                created = getattr(o, created_field, None) if created_field else None
                if created and created >= new_cutoff:
                    label = LABEL.NEW
            if getattr(o, "label", None) != label:
                o.label = label
                o.save(update_fields=["label"])
            labelled += 1
    return labelled
