"""
EngineController — read/write logic for the v2.1.0.0 discovery engine API.

Read endpoints serve pre-computed data: Redis first, DB fallback, re-warm on miss
(never compute rankings at request time). Event endpoints are fire-and-forget writes.
"""
from collections import namedtuple

from django.db.models import F
from django.utils import timezone

from app_ib.Utils.SafeCache import safe_cache as cache

# Lightweight stand-in for a TrendingScore row when the board is empty (see
# _trending_fallback_rows); duck-types the .objectId/.rank/.score access.
_FallbackRank = namedtuple("_FallbackRank", "objectId rank score")

from app_ib.Utils.EngineConfig import (
    ENTITY_TYPE, TRENDING_PERIOD, LEADERBOARD_PERIOD, LEADERBOARD_BOARD, ALGO,
)
from app_ib.algorithms.helpers import get_model, content_type_for, owner_user_id


class _EngineController:

    # ---------------- Trending ----------------
    def trending_entities(self, entity_type, period=TRENDING_PERIOD.DAILY, city=""):
        from app_ib.models import TrendingScore
        ct = content_type_for(entity_type)
        rows = list(TrendingScore.objects.filter(contentType=ct, period=period, city=city or "")
                    .order_by("rank")[:50])
        model = get_model(entity_type)
        if not rows:
            # Cron-populated board is empty. Enqueue the recompute as a background
            # task (never synchronously — the request must not block) and serve a
            # best-effort fallback from the entities' denormalized trendingScore so
            # the section is never empty while the real board warms up.
            from app_ib.algorithms.background import enqueue
            from app_ib.algorithms.scoring import compute_trending_scores
            enqueue("compute_trending_scores", compute_trending_scores)
            rows = self._trending_fallback_rows(model, entity_type)
        qs = model.objects.filter(id__in=[r.objectId for r in rows])
        # Prefetch related data for products to avoid N+1 on category + images.
        # Uses prefetch_related so it is always a single extra query, not N.
        # Guard: only Product has these relations — other entity types remain untouched.
        if entity_type == ENTITY_TYPE.PRODUCT:
            qs = (qs.prefetch_related("category", "productImages")
                    .select_related("business", "business__business_location"))
        elif entity_type == ENTITY_TYPE.SERVICE:
            qs = qs.select_related("business", "business__business_location")
        elif entity_type == ENTITY_TYPE.BUSINESS:
            qs = qs.select_related("business_location")
        objs = {o.id: o for o in qs}
        out = []
        for r in rows:
            o = objs.get(r.objectId)
            if not o:
                continue
            # Base fields — identical to legacy response (existing keys, order preserved)
            item = {
                "entityType": entity_type, "id": o.id,
                "name": _name(o), "slug": getattr(o, "slug", "") or "",
                "imageUrl": _image(o), "rank": r.rank,
                "trendingScore": r.score, "rating": _rating(o),
                "label": getattr(o, "label", "") or "",
            }
            # ── Additive enrichment keys (new in this release) ──────────────────
            # All use getattr with a safe default so non-Product entity types that
            # also flow through this path (business, service, etc.) never error.
            # Frontend ignores keys it doesn't use — no breaking change on the wire.

            # Real view count (Product.viewCount; fallback 0 for entities without it)
            item["viewCount"] = getattr(o, "viewCount", 0) or 0

            # Pricing — displayPrice is the post-discount price; orignalPrice is legacy typo kept as-is
            item["price"] = getattr(o, "displayPrice", None)
            item["originalPrice"] = getattr(o, "orignalPrice", None)

            # Review depth
            item["totalReviews"] = getattr(o, "totalReviews", 0) or 0

            # Category label — first category's lable (note legacy typo); cheap because
            # prefetch_related already loaded the M2M set in a single query above.
            # getattr + all() is safe on models without a 'category' M2M.
            cat_mgr = getattr(o, "category", None)
            if cat_mgr is not None:
                try:
                    first_cat = list(cat_mgr.all())[:1]
                    item["categoryName"] = (first_cat[0].lable or first_cat[0].value) if first_cat else ""
                except Exception:
                    item["categoryName"] = ""
            else:
                item["categoryName"] = ""

            # Stock availability — null stockQuantity means untracked → treat as in stock
            stock_qty = getattr(o, "stockQuantity", None)
            item["inStock"] = True if stock_qty is None else (stock_qty > 0)

            # Product image — _image() returns "" for Products (no coverImageUrl field).
            # Pull the first ProductImage URL when present and imageUrl is still empty.
            if not item["imageUrl"]:
                img_mgr = getattr(o, "productImages", None)
                if img_mgr is not None:
                    try:
                        first_img = list(img_mgr.all())[:1]
                        item["imageUrl"] = first_img[0].image if first_img else ""
                    except Exception:
                        pass

            # ── FEATURED-SHORT panel enrichment (drives the reel modal that the
            # "Hot this week" tiles open). Additive; leaderboard consumers ignore
            # keys they don't use. Joins are prefetched above to avoid N+1. ──
            biz = o if entity_type == ENTITY_TYPE.BUSINESS else getattr(o, "business", None)
            item["business"] = (getattr(biz, "businessName", "") or _name(biz)) if biz else ""
            item["businessId"] = biz.id if biz else None
            loc = getattr(biz, "business_location", None) if biz else None
            item["city"] = getattr(loc, "city", "") if loc else ""
            item["verified"] = bool(getattr(biz, "isVerified", False)) if biz else False
            item["description"] = _clean_desc(getattr(o, "description", "") or getattr(o, "bio", "") or "")

            out.append(item)
        _attach_trending_review_quotes(out)
        return out

    def _trending_fallback_rows(self, model, entity_type):
        """Best-effort stand-in for an empty TrendingScore board: the top entities
        by their denormalized trendingScore (newest as tie-breaker). Shaped like
        TrendingScore rows (objectId/rank/score) so trending_entities consumes it
        unchanged."""
        qs = model.objects.all()
        if entity_type in (ENTITY_TYPE.PRODUCT, ENTITY_TYPE.SERVICE):
            qs = qs.filter(isActive=True)
        top = list(qs.order_by("-trendingScore", "-id")[:50])
        return [_FallbackRank(o.id, i + 1, getattr(o, "trendingScore", 0.0) or 0.0)
                for i, o in enumerate(top)]

    def trending_searches(self, category_fallback=False, min_items=8):
        board = cache.get("trending:searches:24h")
        if board is None:
            # Cache miss: recomputing the 24h search aggregation is a cron-class
            # job, so offload it to the background runner (never block the request)
            # and serve a best-effort fallback below. The nightly cron / the
            # enqueued run re-warm "trending:searches:24h" for the next request.
            from app_ib.algorithms.background import enqueue
            from app_ib.algorithms.aggregation import calculate_trending_searches
            enqueue("calculate_trending_searches", calculate_trending_searches)
            board = []
        board = list(board or [])
        # Top up with business categories so the section is never empty — always
        # on the trending page, and on any caller when the board came back empty
        # (e.g. the cold-cache path above that offloaded the recompute).
        if (category_fallback or not board) and len(board) < min_items:
            from app_ib.models import BusinessCategory
            existing = {b["query"].lower() for b in board}
            cats = BusinessCategory.objects.order_by("-trending", "index")
            for c in cats:
                label = (c.lable or c.value or "").strip()
                if label and label.lower() not in existing:
                    board.append({"query": label, "count": 0, "isCategory": True})
                    existing.add(label.lower())
                if len(board) >= min_items:
                    break
        return board

    def momentum(self, limit=30):
        """Cross-entity 'momentum' board — ANY entity type, ranked by daily national
        trendingScore (business, shop, architect, product, service, catelogue)."""
        from app_ib.models import TrendingScore
        from app_ib.Utils.EngineConfig import TRENDING_PERIOD
        rows = (TrendingScore.objects.filter(period=TRENDING_PERIOD.DAILY, city="", score__gt=0)
                .select_related("contentType").order_by("-score")[:limit * 3])
        out = []
        for r in rows:
            model = r.contentType.model_class()
            obj = model.objects.filter(id=r.objectId).first()
            if not obj:
                continue
            out.append({"entityType": r.contentType.model, "id": obj.id, "name": _name(obj),
                        "slug": getattr(obj, "slug", "") or "", "imageUrl": _image(obj),
                        "trendingScore": r.score, "rating": _rating(obj),
                        "label": getattr(obj, "label", "") or ""})
            if len(out) >= limit:
                break
        return out

    def city_pulse(self, city):
        if city:
            payload = cache.get(f"city_pulse:{city}")
            if payload:
                return payload
        # fallback: national — top businesses by daily national trending
        national = self.trending_entities(ENTITY_TYPE.BUSINESS, TRENDING_PERIOD.DAILY, "")
        return {"city": city or "", "fallback": True,
                "top_businesses": national[:ALGO.CITY_PULSE_TOP_BUSINESSES],
                "trending_searches": self.trending_searches()}

    # ---------------- Leaderboard ----------------
    def leaderboard(self, period=LEADERBOARD_PERIOD.WEEKLY, board=LEADERBOARD_BOARD.COMBINED,
                    entity_types=None):
        from app_ib.models import LeaderboardEntry
        # entity_types filter (e.g. product+service board) re-ranks the subset 1..N
        if entity_types:
            rows = (LeaderboardEntry.objects.filter(boardType=board, period=period,
                                                    entityType__in=entity_types)
                    .order_by("rank")[:ALGO.LEADERBOARD_CACHE_TOP])
            return [{"rank": i, "entityType": e.entityType, "id": e.objectId,
                     "displayName": e.displayName, "slug": e.slug, "imageUrl": e.imageUrl,
                     "score": e.score, "genuineViews": e.genuineViews, "clicks": e.clicks}
                    for i, e in enumerate(rows, start=1)]
        cache_key = f"leaderboard:{board}:{period}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        rows = (LeaderboardEntry.objects.filter(boardType=board, period=period)
                .order_by("rank")[:ALGO.LEADERBOARD_CACHE_TOP])
        data = [{
            "rank": e.rank, "entityType": e.entityType, "id": e.objectId,
            "displayName": e.displayName, "slug": e.slug, "imageUrl": e.imageUrl,
            "score": e.score, "genuineViews": e.genuineViews, "clicks": e.clicks,
        } for e in rows]
        cache.set(cache_key, data, 25 * 60 * 60)  # 25h warm
        return data

    # ---------------- Discovery ----------------
    def most_saved(self):
        from app_ib.algorithms.aggregation import ensure_discovery_cache_warm
        items = cache.get("discovery:most_saved")
        if items is None:
            # warm returns the snapshot items directly so this works even when
            # the cache backend itself is unavailable (SafeCache degrades to miss)
            items = ensure_discovery_cache_warm() or []
        return self._hydrate_saved(items)

    def _hydrate_saved(self, items):
        from django.contrib.contenttypes.models import ContentType
        out = []
        for it in items:
            ct = ContentType.objects.filter(id=it.get("contentType")).first()
            if not ct:
                continue
            obj = ct.model_class().objects.filter(id=it["objectId"]).first()
            if not obj:
                continue
            out.append({"entityType": ct.model, "id": obj.id, "name": _name(obj),
                        "slug": getattr(obj, "slug", "") or "", "imageUrl": _image(obj),
                        "saveCount": it.get("saveCount", 0)})
        return out

    def behind_the_trend(self):
        from app_ib.models import BehindTheTrendStory
        today = timezone.now().date()
        stories = BehindTheTrendStory.objects.filter(isPublished=True).order_by("rank")
        latest = stories.filter(snapshotDate=today)
        stories = latest if latest.exists() else stories[:ALGO.BEHIND_TREND_TOP_N]
        return [{
            "businessId": s.business_id, "rank": s.rank, "rankFrom": s.rankFrom, "rankTo": s.rankTo,
            "windowLabel": s.windowLabel, "imageUrl": s.imageUrl,
            "enquiryGrowthPct": s.enquiryGrowthPct, "headline": s.headline,
            "eyebrow": s.eyebrow, "storyTitle": s.storyTitle, "storyBody": s.storyBody,
            "trendTags": s.trendTags,
        } for s in stories]

    # ---------------- Completion ----------------
    def completion(self, entity_type, object_id):
        from app_ib.algorithms.completion import compute_completion
        obj = get_model(entity_type).objects.filter(id=object_id).first()
        if not obj:
            return None
        return compute_completion(entity_type, obj)

    # ---------------- Events (fire-and-forget writes) ----------------
    def track_view(self, entity_type, object_id, user=None, session_id="",
                   city="", state="", dwell_seconds=None):
        from app_ib.models import ViewEvent
        ct = content_type_for(entity_type)
        ViewEvent.objects.create(contentType=ct, objectId=object_id,
                                 user=user if (user and user.is_authenticated) else None,
                                 sessionId=session_id or "", city=city, state=state,
                                 dwellSeconds=dwell_seconds)
        get_model(entity_type).objects.filter(id=object_id).update(viewCount=F("viewCount") + 1)
        if user and user.is_authenticated:
            from app_ib.algorithms.state import record_recently_viewed
            record_recently_viewed(user, entity_type, object_id)
        # Inbound engagement: "someone viewed your <entity>" (fire-and-forget).
        try:
            from app_ib.algorithms.state import record_engagement
            from app_ib.Utils.EngineConfig import ENGAGEMENT_VERB
            record_engagement(ENGAGEMENT_VERB.VIEW, entity_type, object_id, actor=user)
        except Exception:
            pass
        return True

    def track_click(self, entity_type, object_id, click_type, user=None, session_id=""):
        from app_ib.models import ClickEvent
        ct = content_type_for(entity_type)
        ClickEvent.objects.create(contentType=ct, objectId=object_id, clickType=click_type,
                                  user=user if (user and user.is_authenticated) else None,
                                  sessionId=session_id or "")
        # Inbound engagement: high-intent clicks (whatsapp/call/website) → feed row.
        try:
            from app_ib.algorithms.state import record_engagement
            from app_ib.Utils.EngineConfig import ENGAGEMENT_VERB
            verb = ENGAGEMENT_VERB.FROM_CLICK.get(click_type)
            if verb:
                record_engagement(verb, entity_type, object_id, actor=user)
        except Exception:
            pass
        return True

    def track_search(self, query, result_count=0, city="", state="", user=None, session_id=""):
        from app_ib.models import SearchEvent
        from app_ib.algorithms.text import normalize
        ev = SearchEvent.objects.create(
            query=query[:500], normalizedQuery=normalize(query)[:500],
            resultCount=result_count, city=city, state=state,
            user=user if (user and user.is_authenticated) else None, sessionId=session_id or "")
        return ev.id

    # ---------------- Saved / recently viewed / notifications ----------------
    def toggle_saved(self, user, entity_type, object_id):
        from app_ib.algorithms.state import toggle_saved
        return toggle_saved(user, entity_type, object_id)

    def list_saved(self, user):
        from app_ib.models import SavedItem
        out = []
        for s in SavedItem.objects.filter(user=user).order_by("-timestamp")[:100]:
            obj = s.contentType.model_class().objects.filter(id=s.objectId).first()
            if obj:
                out.append({"entityType": s.contentType.model, "id": obj.id,
                            "objectId": s.objectId, "name": _name(obj),
                            "imageUrl": _image(obj),
                            "slug": getattr(obj, "slug", "") or "",
                            "savedAt": s.timestamp.isoformat() if s.timestamp else None})
        return out

    def recently_viewed(self, user):
        from app_ib.models import RecentlyViewed
        out = []
        for r in RecentlyViewed.objects.filter(user=user).order_by("-viewedAt")[:ALGO.RECENTLY_VIEWED_CAP]:
            obj = r.contentType.model_class().objects.filter(id=r.objectId).first()
            if obj:
                count, count_label = _rv_count(obj)
                out.append({"entityType": r.contentType.model, "id": obj.id,
                            # rowId = the RecentlyViewed PK — lets the client delete
                            # THIS visit row (per-item remove, task 45).
                            "rowId": r.id,
                            "objectId": r.objectId, "name": _name(obj),
                            "imageUrl": _image(obj),
                            "slug": getattr(obj, "slug", "") or "",
                            "category": _rv_category(obj),
                            "rating": _rv_rating(obj),
                            "count": count, "countLabel": count_label,
                            "price": _rv_price(obj),
                            "viewedAt": r.viewedAt.isoformat()})
        return out

    def recently_viewed_export_rows(self, user):
        """Same query/ordering as recently_viewed() (RecentlyViewed rows for
        this user, newest first, capped at ALGO.RECENTLY_VIEWED_CAP) but
        stripped to only the two fields safe for a CSV export: the display
        name and the raw viewedAt datetime. No id/objectId/slug/entityType —
        the view formats viewedAt for display."""
        from app_ib.models import RecentlyViewed
        out = []
        for r in RecentlyViewed.objects.filter(user=user).order_by("-viewedAt")[:ALGO.RECENTLY_VIEWED_CAP]:
            obj = r.contentType.model_class().objects.filter(id=r.objectId).first()
            if obj:
                out.append((_name(obj), r.viewedAt))
        return out

    def notifications(self, user):
        from app_ib.models import Notification
        return [{"id": n.id, "type": n.type, "title": n.title, "body": n.body,
                 "groupCount": n.groupCount, "actionUrl": n.actionUrl,
                 "timestamp": n.timestamp.isoformat()}
                for n in Notification.objects.filter(user=user).order_by("-timestamp")[:50]]

    def unread_count(self, user):
        from app_ib.models import Notification
        return Notification.objects.filter(user=user).count()


# ---- small display helpers ----
def _name(o):
    return (getattr(o, "businessName", None) or getattr(o, "name", None)
            or getattr(o, "title", None) or str(o))


def _image(o):
    return (getattr(o, "coverImageUrl", None) or getattr(o, "coverImage", None)
            or getattr(o, "catelougeImage", None) or "")


def _rating(o):
    return getattr(o, "ratingValue", None) if hasattr(o, "ratingValue") else getattr(o, "rating", 0.0)


# ---- recently-viewed row enrichment (all defensive: never raise) ----
# obj may be a Business / Product / Service / Shop / Architect — fields differ,
# so every helper is getattr-with-fallback + try/except → empty/zero default.
def _cat_label(c):
    # Category models use the misspelled `lable`; also cover label/name/value.
    return (getattr(c, "lable", None) or getattr(c, "label", None)
            or getattr(c, "name", None) or getattr(c, "value", None) or "") or ""


def _rv_category(o):
    try:
        cat = getattr(o, "category", None)  # products/services: M2M ProductCategory
        if cat is not None:
            first = cat.all().first() if hasattr(cat, "all") else cat
            if first is not None:
                return _cat_label(first)
        for attr in ("segments", "businessCategory"):  # businesses
            mgr = getattr(o, attr, None)
            if mgr is not None and hasattr(mgr, "all"):
                first = mgr.all().first()
                if first is not None:
                    return _cat_label(first)
        return getattr(o, "label", "") or ""  # architects/shops
    except Exception:
        return ""


def _rv_rating(o):
    try:
        return float(getattr(o, "ratingValue", getattr(o, "rating", 0)) or 0)
    except Exception:
        return 0.0


def _rv_count(o):
    try:
        projects = getattr(o, "projects", None)  # businesses/architects (reverse FK)
        if projects is not None and hasattr(projects, "count"):
            return projects.count(), "projects"
        reviews = getattr(o, "totalReviews", None)  # products/services/shops
        if reviews is not None:
            return int(reviews or 0), "reviews"
        lead = getattr(o, "leadCount", None)
        if lead is not None:
            return int(lead or 0), "projects"
        return 0, ""
    except Exception:
        return 0, ""


def _rv_price(o):
    # Products/services carry a price; businesses/architects/shops don't.
    try:
        if not (hasattr(o, "displayPrice") or hasattr(o, "orignalPrice")):
            return ""
        val = float(getattr(o, "displayPrice", None) or getattr(o, "orignalPrice", 0) or 0)
        return ("₹" + format(int(round(val)), ",")) if val > 0 else ""
    except Exception:
        return ""


def _clean_desc(text, limit=220):
    """Plain-text, length-capped description for the reel panel — product/service
    descriptions are rich-text HTML (quill), so strip tags + collapse whitespace."""
    from django.utils.html import strip_tags
    t = " ".join(strip_tags(text or "").split()).strip()
    return (t[:limit].rstrip() + "…") if len(t) > limit else t


def _attach_trending_review_quotes(items):
    """Attach each item's owning-business most-recent approved review as
    `reviewQuote` (the reel modal 'Top review' block). One bounded query for all
    businesses in the batch; items without a business get an empty quote."""
    biz_ids = {i.get("businessId") for i in items if i.get("businessId")}
    quotes = {}
    if biz_ids:
        from app_ib.models import Review
        for rv in (Review.objects.filter(business_id__in=biz_ids, isApproved=True, isDeleted=False)
                   .exclude(body="").order_by("business_id", "-timestamp")
                   .values("business_id", "body")):
            quotes.setdefault(rv["business_id"], rv["body"])
    for i in items:
        i["reviewQuote"] = quotes.get(i.get("businessId"), "")


ENGINE_CONTROLLER = _EngineController()
