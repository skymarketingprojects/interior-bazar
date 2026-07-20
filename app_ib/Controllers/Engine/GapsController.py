"""
GapsController — business logic for the 12 API-contract gap endpoints (v2.1.1).

Areas covered:
  1.  trending/services/
  2.  trending/categories/
  3.  trending/kpi/
  4.  saved/check/
  5.  recently-viewed/clear/
  6.  dashboard/kpis/          (+ firstResponseSeconds wired in ChatController)
  7.  analytics/chart/
  8.  shop/<id|slug>/ + shops/ + architect/<id|slug>/ + architects/
  9.  videos CRUD
  10. leads/prioritized/ + leads/<id>/accept|decline/
  11. ads/?page=  + ads/<id>/click/
  12. SSE ?token= auth (handled in EngineGapsView, not here)
"""
import json
import logging
from app_ib.Utils.SafeCache import safe_cache as cache
from django.db import transaction
from django.db.models import F, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta, date

logger = logging.getLogger(__name__)


def _parse_tag_list(raw):
    """Tags are stored either as a Python-repr list string (old prod:
    "['Custom Interiors', 'LED Lighting']") or a plain comma-separated string
    (v3 create form). Same defensive parse as PRODUCTS_V3_CONTROLLER._tags."""
    if not raw:
        return []
    try:
        parsed = json.loads(str(raw).replace("'", '"'))
        return [str(t) for t in parsed] if isinstance(parsed, list) else []
    except Exception:
        return [t.strip() for t in str(raw).split(",") if t.strip()]

from app_ib.Utils.EngineConfig import (
    ENTITY_TYPE, TRENDING_PERIOD, CONVERSATION_STATUS,
)
from app_ib.algorithms.helpers import get_model, content_type_for
from app_ib.Controllers.Engine.CrudController import NotFound_, PermissionError_, Conflict_

# 1-hour TTL for trending/categories caches
_CACHE_1H = 60 * 60
# 15-minute TTL for dashboard KPIs
_CACHE_15M = 15 * 60
# 10-minute TTL for the home proof-band stats (trending/kpi)
_CACHE_10M = 10 * 60


# ---------------------------------------------------------------------------
# 1. Trending services
# ---------------------------------------------------------------------------
def trending_services(period=TRENDING_PERIOD.WEEKLY, city=""):
    """Mirror of trending/products/ but for Service model."""
    from app_ib.models import TrendingScore
    ct = content_type_for(ENTITY_TYPE.SERVICE)
    # fallback: try weekly first, fall back to daily
    rows = list(TrendingScore.objects.filter(
        contentType=ct, period=period, city=city or "").order_by("rank")[:50])
    if not rows and period == TRENDING_PERIOD.WEEKLY:
        rows = list(TrendingScore.objects.filter(
            contentType=ct, period=TRENDING_PERIOD.DAILY, city=city or "").order_by("rank")[:50])

    model = get_model(ENTITY_TYPE.SERVICE)
    objs = {o.id: o for o in model.objects.filter(id__in=[r.objectId for r in rows])}
    out = []
    for r in rows:
        o = objs.get(r.objectId)
        if not o:
            continue
        out.append({
            "entityType": ENTITY_TYPE.SERVICE,
            "id": o.id,
            "name": getattr(o, "title", "") or str(o),
            "slug": getattr(o, "slug", "") or "",
            "imageUrl": _service_image(o),
            "rank": r.rank,
            "trendingScore": r.score,
            "rating": getattr(o, "ratingValue", 0.0) or getattr(o, "rating", 0.0) or 0.0,
            "label": getattr(o, "label", "") or "",
        })
    return out


def _service_image(o):
    for attr in ("coverImageUrl", "coverImage", "imageSQUrl", "imageRTUrl"):
        v = getattr(o, attr, None)
        if v:
            return v
    imgs = getattr(o, "serviceImages", None)
    if imgs:
        first = imgs.order_by("index").first()
        if first:
            return getattr(first, "imageUrl", "") or ""
    return ""


# ---------------------------------------------------------------------------
# 2. Trending categories
# ---------------------------------------------------------------------------
def trending_categories(cat_type="business", period=TRENDING_PERIOD.WEEKLY, limit=12):
    cache_key = f"trending:categories:v2:{cat_type}:{period}:{limit}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    result = _compute_trending_categories(cat_type, period, limit)
    cache.set(cache_key, result, _CACHE_1H)
    return result


def _compute_trending_categories(cat_type, period, limit):
    if cat_type == "business":
        return _business_categories(period, limit)
    # product categories fallback
    return _product_categories(period, limit)


def _business_categories(period, limit):
    from app_ib.models import BusinessCategory, Business, TrendingScore
    try:
        biz_ct = content_type_for(ENTITY_TYPE.BUSINESS)
        # find businesses with TrendingScore rows
        scored_rows = TrendingScore.objects.filter(
            contentType=biz_ct, period=period, city=""
        ).values_list("objectId", "score")
        if not scored_rows.exists():
            # fallback: weekly → daily
            if period == TRENDING_PERIOD.WEEKLY:
                scored_rows = TrendingScore.objects.filter(
                    contentType=biz_ct, period=TRENDING_PERIOD.DAILY, city=""
                ).values_list("objectId", "score")

        score_map = {oid: sc for oid, sc in scored_rows}

        if score_map:
            # aggregate by category
            from collections import defaultdict
            cat_scores = defaultdict(lambda: {"score": 0.0, "entityCount": 0, "cat": None})
            for biz in (Business.objects.filter(id__in=score_map.keys())
                        .prefetch_related("businessCategory")):
                s = score_map.get(biz.id, 0)
                for cat in biz.businessCategory.all():
                    cat_scores[cat.id]["score"] += s
                    cat_scores[cat.id]["entityCount"] += 1
                    cat_scores[cat.id]["cat"] = cat

            cats_out = []
            for cid, info in sorted(cat_scores.items(), key=lambda x: -x[1]["score"]):
                c = info["cat"]
                if not c:
                    continue
                cats_out.append({
                    "id": c.id,
                    "name": c.lable or c.value or "",
                    "value": c.value or "",
                    "imageUrl": c.imageSQUrl or c.imageRTUrl or "",
                    "entityCount": info["entityCount"],
                    "score": round(info["score"], 2),
                    "rank": len(cats_out) + 1,
                })
                if len(cats_out) >= limit:
                    break
            if cats_out:
                return cats_out
    except Exception:
        pass

    # ultimate fallback: categories with trending=True ordered by index
    cats = BusinessCategory.objects.filter(isActive=True, trending=True).order_by("index")[:limit]
    return [{
        "id": c.id,
        "name": c.lable or c.value or "",
        "value": c.value or "",
        "imageUrl": c.imageSQUrl or c.imageRTUrl or "",
        "entityCount": 0,
        "score": 0.0,
        "rank": i + 1,
    } for i, c in enumerate(cats)]


def _product_categories(period, limit):
    """Product category trending — best-effort, never 500."""
    try:
        from interior_products.models import ProductCategory
        cats = ProductCategory.productOnes().order_by("index")[:limit]
        return [{
            "id": c.id,
            "name": getattr(c, "lable", None) or getattr(c, "value", None) or str(c),
            "value": getattr(c, "value", None) or "",
            "imageUrl": getattr(c, "imageSQUrl", None) or getattr(c, "imageRTUrl", None) or "",
            "entityCount": 0,
            "score": 0.0,
            "rank": i + 1,
        } for i, c in enumerate(cats)]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# 3. Trending KPI
# ---------------------------------------------------------------------------
def trending_kpi():
    """Home proof-band stats, cached 10 minutes. On expiry a SINGLE-FLIGHT lock
    ensures only one request recomputes; every other concurrent request serves
    the last-known ("stale") copy instead of also hitting the DB — so a burst of
    home traffic on cache expiry can't stampede the aggregate queries.

    ponytail: get→set cache lock (not atomic) + a longer-lived stale copy. Worst
    case is a couple of extra recomputes, never a herd; swap in a Redis SETNX
    lock only if that ever measurably matters.
    """
    cache_key = "trending:kpi"
    lock_key = "trending:kpi:lock"
    stale_key = "trending:kpi:stale"

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # cache expired -> single-flight: if another request is already recomputing,
    # serve the stale copy (kept alive far longer than the fresh TTL).
    if cache.get(lock_key):
        stale = cache.get(stale_key)
        if stale is not None:
            return stale

    cache.set(lock_key, 1, 30)  # 30s guard so a crashed recompute can't wedge it
    try:
        result = _compute_kpi()
        cache.set(cache_key, result, _CACHE_10M)
        cache.set(stale_key, result, _CACHE_10M * 6)  # ~1h stale window for herds
        return result
    finally:
        cache.delete(lock_key)


def _compute_kpi():
    from app_ib.models import Business, Review, LeadQuery
    try:
        from interior_products.models import Product, Service, Catelogue
    except Exception:
        Product = Service = Catelogue = None

    from app_ib.models import Shop, Architect

    def _count(model, **kwargs):
        try:
            return model.objects.filter(**kwargs).count()
        except Exception:
            return 0

    # Business has no isActive flag — count all rows
    businesses = _count(Business)
    products = _count(Product) if Product else 0
    services = _count(Service) if Service else 0
    catalogues = _count(Catelogue) if Catelogue else 0
    shops = _count(Shop, isActive=True)
    architects = _count(Architect, isActive=True)
    reviews = _count(Review, isDeleted=False, isApproved=True)
    leads = _count(LeadQuery)
    # distinct cities across businesses (Location is a reverse 1:1 on Business)
    try:
        cities = (Business.objects
                  .values("business_location__city")
                  .distinct()
                  .exclude(business_location__city="")
                  .exclude(business_location__city__isnull=True)
                  .count())
    except Exception:
        cities = 0

    # ── prototype proof-band stats (real data, slightly rounded) ──
    from django.db.models import Avg
    # ponytail: avg deal value used ONLY to express "projects value facilitated"
    # in ₹ (no per-deal value is stored). It multiplies a REAL count of completed
    # (won) leads, so the figure moves with real data; tune here when deal values
    # become available.
    AVG_PROJECT_VALUE_INR = 250000  # ₹2.5L average project

    verified = _count(Business, isVerified=True)
    won = _count(LeadQuery, stage="won")
    try:
        avg_rating = Business.objects.filter(ratingValue__gt=0).aggregate(a=Avg("ratingValue"))["a"] or 0.0
    except Exception:
        avg_rating = 0.0
    try:
        states = (Business.objects
                  .exclude(business_location__locationState__isnull=True)
                  .values("business_location__locationState").distinct().count())
    except Exception:
        states = 0
    try:
        avg_resp_sec = Business.objects.filter(avgResponseSeconds__isnull=False) \
            .aggregate(a=Avg("avgResponseSeconds"))["a"]
    except Exception:
        avg_resp_sec = None

    def _floor_to(n, step):
        return (n // step) * step if n and n >= step else n

    return {
        # raw counts (kept for existing consumers)
        "businesses": businesses,
        "products": products,
        "services": services,
        "catalogues": catalogues,
        "shops": shops,
        "architects": architects,
        "reviews": reviews,
        "leads": leads,
        "cities": cities,
        # ── proof-band (matches the prototype's .proof-band) ──
        "verifiedBusinesses": _floor_to(verified, 10),          # e.g. 523 -> 520
        "completedProjects": won,                               # real won leads
        "projectsValueCr": round(won * AVG_PROJECT_VALUE_INR / 1e7, 1),  # ₹Cr facilitated
        "avgRating": round(avg_rating, 1),                      # 4.8
        "statesCovered": states,                               # distinct states
        "avgResponseHours": round((avg_resp_sec or 0) / 3600.0, 1) if avg_resp_sec else None,
        "conversionRate": round(won / leads, 3) if leads else 0.0,  # won/total
    }


# ---------------------------------------------------------------------------
# 4. Saved check
# ---------------------------------------------------------------------------
def saved_check(user, entity_type, object_id):
    from app_ib.models import SavedItem
    ct = content_type_for(entity_type)
    exists = SavedItem.objects.filter(user=user, contentType=ct, objectId=object_id).exists()
    return {"isSaved": exists}


# ---------------------------------------------------------------------------
# 5. Recently-viewed clear
# ---------------------------------------------------------------------------
def recently_viewed_clear(user):
    from app_ib.models import RecentlyViewed
    deleted, _ = RecentlyViewed.objects.filter(user=user).delete()
    return {"cleared": deleted}


def recently_viewed_remove(user, row_id):
    """Delete a single RecentlyViewed row (per-item remove, task 45). Scoped to the
    caller's own rows, so a bad/foreign id simply deletes nothing (removed=0)."""
    from app_ib.models import RecentlyViewed
    deleted, _ = RecentlyViewed.objects.filter(user=user, id=row_id).delete()
    return {"removed": deleted}


# Default notification/privacy toggles when the user hasn't saved settings yet.
_DEFAULT_SETTINGS = {
    "notifications": {
        "connectionUpdates": True,
        "newMessages": True,
        "weeklyDigest": False,
        "marketing": False,
        # Seller profile "Communication preferences" toggles (task 7). Kept in the
        # same notifications block so the existing get/update merge handles them;
        # the buyer Settings view ignores keys it doesn't render.
        "enquiryAlerts": True,
        "responseReminders": True,
        "weeklyReport": True,
        "marketingUpdates": False,
    },
    "privacy": {
        "publicProfile": True,
        "showOnline": True,
        "personalisedRecs": True,
    },
    # Which 2FA methods the user has enabled (task 65c). This persists the seller's
    # choice; the actual challenge/enrollment flow is a separate, future feature.
    "twoFactor": {
        "sms": False,
        "email": False,
        "authenticator": False,
    },
}


def get_user_settings(user):
    """Buyer dashboard Settings — notification/privacy toggles (JSON on the user)
    merged over defaults, plus language/currency from the dedicated fields."""
    saved = user.settings if isinstance(user.settings, dict) else {}
    notifications = {**_DEFAULT_SETTINGS["notifications"], **(saved.get("notifications") or {})}
    privacy = {**_DEFAULT_SETTINGS["privacy"], **(saved.get("privacy") or {})}
    two_factor = {**_DEFAULT_SETTINGS["twoFactor"], **(saved.get("twoFactor") or {})}
    return {
        "notifications": notifications,
        "privacy": privacy,
        "twoFactor": two_factor,
        # Free-form seller preferences (e.g. country) with no dedicated column.
        "prefs": saved.get("prefs") or {},
        "language": user.preferred_language or "en",
        "currency": user.preferred_currency or "INR",
    }


def update_user_settings(user, data):
    """Merge-update the user's settings. notifications/privacy dicts merge into the
    JSON field; language/currency write to the dedicated CustomUser columns."""
    data = data or {}
    saved = user.settings if isinstance(user.settings, dict) else {}
    notifications = {**_DEFAULT_SETTINGS["notifications"], **(saved.get("notifications") or {})}
    privacy = {**_DEFAULT_SETTINGS["privacy"], **(saved.get("privacy") or {})}
    two_factor = {**_DEFAULT_SETTINGS["twoFactor"], **(saved.get("twoFactor") or {})}
    prefs = dict(saved.get("prefs") or {})
    if isinstance(data.get("notifications"), dict):
        notifications.update({k: bool(v) for k, v in data["notifications"].items() if k in notifications})
    if isinstance(data.get("privacy"), dict):
        privacy.update({k: bool(v) for k, v in data["privacy"].items() if k in privacy})
    if isinstance(data.get("twoFactor"), dict):
        two_factor.update({k: bool(v) for k, v in data["twoFactor"].items() if k in two_factor})
    if isinstance(data.get("prefs"), dict):
        # Free-form string prefs; cap key/value length to keep the JSON bounded.
        prefs.update({str(k)[:40]: str(v)[:80] for k, v in data["prefs"].items()})
    user.settings = {"notifications": notifications, "privacy": privacy,
                     "twoFactor": two_factor, "prefs": prefs}
    update_fields = ["settings"]
    if data.get("language"):
        user.preferred_language = str(data["language"])[:10]
        update_fields.append("preferred_language")
    if data.get("currency"):
        user.preferred_currency = str(data["currency"])[:3]
        update_fields.append("preferred_currency")
    user.save(update_fields=update_fields)
    return get_user_settings(user)


def deactivate_account(user):
    """Deactivate (not delete) the caller's account — flips is_active off so they
    can no longer authenticate. The client signs the user out afterwards."""
    user.is_active = False
    user.save(update_fields=["is_active"])
    return {"deactivated": True}


# ── Autogrowth keywords (seller dashboard, task 58) ──
# Keyword capacity per plan tier (Subscription.tier: higher = better plan).
_AUTOGROWTH_TIER_LIMITS = {0: 5, 1: 15, 2: 30, 3: 60}
_AUTOGROWTH_FREE_LIMIT = 3

# Setup caps per tier for the Autogrowth ▸ Setup tab (S8). None = unlimited.
_AUTOGROWTH_SETUP_CAPS = {
    0: {"states": 2,    "segments": 2,    "depth": "2-step", "exclusive": False},
    1: {"states": 2,    "segments": 2,    "depth": "3-step", "exclusive": False},
    2: {"states": 5,    "segments": 3,    "depth": "4-step", "exclusive": True},
    3: {"states": None, "segments": None, "depth": "4-step", "exclusive": True},
}


def _autogrowth_plan(user):
    """The seller's active plan (name, tier, keyword limit, setup caps). Falls back to a
    small free-tier cap when there's no active plan."""
    from app_ib.models import BusinessPlan
    from django.db.models import Q
    bp = (BusinessPlan.objects.filter(Q(user=user) | Q(business__user=user), isActive=True)
          .select_related("plan").order_by("-plan__tier").first())
    if bp and bp.plan:
        tier = bp.plan.tier or 0
        caps = _AUTOGROWTH_SETUP_CAPS.get(tier, _AUTOGROWTH_SETUP_CAPS[0])
        return {
            "planName": bp.plan.title or "Plan",
            "limit": _AUTOGROWTH_TIER_LIMITS.get(tier, _AUTOGROWTH_FREE_LIMIT),
            "statesCap": caps["states"],
            "segmentsCap": caps["segments"],
            "depth": caps["depth"],
            "exclusive": caps["exclusive"],
        }
    caps = _AUTOGROWTH_SETUP_CAPS[0]
    return {
        "planName": "Free",
        "limit": _AUTOGROWTH_FREE_LIMIT,
        "statesCap": caps["states"],
        "segmentsCap": caps["segments"],
        "depth": caps["depth"],
        "exclusive": caps["exclusive"],
    }


def autogrowth_list(user):
    from app_ib.engine_models import AutogrowthKeyword
    plan = _autogrowth_plan(user)
    kws = list(AutogrowthKeyword.objects.filter(user=user).order_by("-id")
               .values("id", "term"))
    return {
        "keywords": kws,
        "quota": {"used": len(kws), "limit": plan["limit"], "planName": plan["planName"]},
        "caps": {
            "states": plan["statesCap"],
            "segments": plan["segmentsCap"],
            "terms": plan["limit"],
            "depth": plan["depth"],
            "exclusive": plan["exclusive"],
        },
    }


def autogrowth_add(user, term):
    from app_ib.engine_models import AutogrowthKeyword
    term = (term or "").strip()[:100]
    if not term:
        raise Conflict_("keyword is empty")
    plan = _autogrowth_plan(user)
    if AutogrowthKeyword.objects.filter(user=user).count() >= plan["limit"]:
        raise Conflict_(f"Your {plan['planName']} plan allows {plan['limit']} keywords. Upgrade to add more.")
    # unique per (user, term) — treat a duplicate as a no-op success
    kw, _created = AutogrowthKeyword.objects.get_or_create(
        user=user, term=term, defaults={"business": _first_business(user)})
    return autogrowth_list(user)


def autogrowth_remove(user, keyword_id):
    from app_ib.engine_models import AutogrowthKeyword
    AutogrowthKeyword.objects.filter(user=user, id=keyword_id).delete()
    return autogrowth_list(user)


def _first_business(user):
    from app_ib.models import Business
    return Business.objects.filter(user=user).first()


def change_plan(user, entity_type, target_plan_id, target_cycle_id=None):
    """In-dashboard plan change (task 61). Money-safe: an UPGRADE (higher tier, or
    no active plan) requires payment → the client routes to checkout; a DOWNGRADE
    to an equal/lower tier is switched immediately (no extra charge, since it's an
    already-paid-for-or-cheaper tier). Target resolved as (planId, cycleId) — the
    cycle's price/durationMonths are snapshotted on the row. Business plans only."""
    from app_ib.models import BusinessPlan, Subscription, PlanBillingCycle
    from django.db.models import Q
    target = Subscription.objects.filter(id=target_plan_id, is_delete=False).first()
    if not target:
        raise NotFound_("plan not found")
    target_tier = target.tier or 0
    active_plans = list(BusinessPlan.objects.filter(Q(user=user) | Q(business__user=user), isActive=True)
                        .select_related("plan"))
    # Highest tier the user currently holds (unambiguous — no reliance on NULL ordering).
    current_tier = max([(bp.plan.tier or 0) for bp in active_plans if bp.plan_id], default=-1)
    if not active_plans or target_tier > current_tier:
        # Upgrade / first purchase — must go through the paid checkout flow.
        return {"requiresPayment": True, "targetPlanId": target.id,
                "targetCycleId": target_cycle_id, "targetPlanName": target.title or "Plan"}
    # Downgrade (or same tier): switch the highest-tier active plan immediately —
    # no additional charge (moving to an equal/cheaper, already-paid tier).
    cyc = (PlanBillingCycle.objects.filter(plan_id=target.id, id=target_cycle_id, isActive=True).first()
           if target_cycle_id else None)
    if not cyc:
        cyc = PlanBillingCycle.objects.filter(plan_id=target.id, isActive=True).order_by("durationMonths").first()
    holder = max(active_plans, key=lambda bp: (bp.plan.tier or 0) if bp.plan_id else -1)
    holder.plan = target
    fields = ["plan"]
    if cyc:
        holder.amount = str(int(cyc.price)) if cyc.price == cyc.price.to_integral_value() else str(cyc.price)
        holder.durationMonths = int(cyc.durationMonths)
        fields += ["amount", "durationMonths"]
    holder.save(update_fields=fields)
    return {"requiresPayment": False, "changed": True,
            "planName": target.title or "Plan", "tier": target_tier}


def mark_all_notifications_read(user):
    """Notifications are an unread-only store (deleted on read), so 'mark all read'
    clears the user's notification rows → unread count drops to 0 (task 57c)."""
    from app_ib.models import Notification
    deleted, _ = Notification.objects.filter(user=user).delete()
    return {"cleared": deleted}


def list_my_feedback(user):
    """The authenticated user's own submitted reports/feedback, newest first
    (buyer dashboard "Reports & feedback", task 48)."""
    from app_ib.models import Feedback
    rows = Feedback.objects.filter(user=user).order_by("-timestamp")
    return [{
        "id": f.id,
        "contact": f.contact or "",
        "feedback": f.feedback or "",
        "status": f.status or "",
        "timestamp": f.timestamp.isoformat() if f.timestamp else "",
    } for f in rows]


# ---------------------------------------------------------------------------
# 6. Dashboard KPIs
# ---------------------------------------------------------------------------
def dashboard_kpis(user, window_days=7):
    cache_key = f"dashboard:kpis:{user.id}:{window_days}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    result = _compute_dashboard_kpis(user, window_days)
    cache.set(cache_key, result, _CACHE_15M)
    return result


def _compute_dashboard_kpis(user, window_days):
    from app_ib.models import BusinessAnalytics, Conversation, Shop, Business
    now = timezone.now()
    window_start = now - timedelta(days=window_days)
    prev_start = window_start - timedelta(days=window_days)

    # Get user's businesses
    biz_qs = Business.objects.filter(user=user)
    biz_ids = list(biz_qs.values_list("id", flat=True))

    # Helper: sum analytics field across user's businesses + shops over a window
    def _analytics_sum(field, start, end, biz_ids_list):
        from django.contrib.contenttypes.models import ContentType
        try:
            biz_ct = ContentType.objects.get_for_model(Business)
        except Exception:
            return 0
        agg = (BusinessAnalytics.objects.filter(
            contentType=biz_ct,
            objectId__in=biz_ids_list,
            date__gte=start.date(),
            date__lte=end.date()
        ).aggregate(total=Sum(field))["total"] or 0)
        return agg

    def _daily_sparkline(field, start, end, biz_ids_list):
        from django.contrib.contenttypes.models import ContentType
        try:
            biz_ct = ContentType.objects.get_for_model(Business)
        except Exception:
            return [0] * window_days
        rows = (BusinessAnalytics.objects.filter(
            contentType=biz_ct,
            objectId__in=biz_ids_list,
            date__gte=start.date(),
            date__lte=end.date()
        ).values("date").annotate(v=Sum(field)))
        by_date = {r["date"]: r["v"] for r in rows}
        out = []
        for i in range(window_days):
            d = (start + timedelta(days=i)).date()
            out.append(by_date.get(d, 0))
        return out

    def _delta(curr, prev):
        if prev == 0:
            return {"pct": None, "isImprovement": True, "label": "new"}
        pct = round((curr - prev) / prev * 100)
        return {"pct": pct, "isImprovement": pct >= 0}

    # --- Enquiries ---
    enq_curr = _analytics_sum("leadCount", window_start, now, biz_ids)
    enq_prev = _analytics_sum("leadCount", prev_start, window_start, biz_ids)
    enq_spark = _daily_sparkline("leadCount", window_start, now, biz_ids)

    # --- New connections (conversations created in window for user's businesses) ---
    conn_curr = Conversation.objects.filter(
        business_id__in=biz_ids,
        createdAt__gte=window_start, createdAt__lte=now
    ).count()
    conn_prev = Conversation.objects.filter(
        business_id__in=biz_ids,
        createdAt__gte=prev_start, createdAt__lt=window_start
    ).count()
    conn_spark = []
    for i in range(window_days):
        ds = window_start + timedelta(days=i)
        de = ds + timedelta(days=1)
        conn_spark.append(
            Conversation.objects.filter(business_id__in=biz_ids,
                                        createdAt__gte=ds, createdAt__lt=de).count()
        )

    # --- New listings (Shop rows created in window for user) ---
    list_curr = Shop.objects.filter(user=user, timestamp__gte=window_start, timestamp__lte=now).count()
    list_prev = Shop.objects.filter(user=user, timestamp__gte=prev_start, timestamp__lt=window_start).count()
    list_spark = []
    for i in range(window_days):
        ds = window_start + timedelta(days=i)
        de = ds + timedelta(days=1)
        list_spark.append(Shop.objects.filter(user=user, timestamp__gte=ds, timestamp__lt=de).count())

    # --- Avg response time (hours) ---
    resp_qs_curr = Conversation.objects.filter(
        business_id__in=biz_ids,
        firstResponseSeconds__isnull=False,
        createdAt__gte=window_start, createdAt__lte=now
    )
    resp_qs_prev = Conversation.objects.filter(
        business_id__in=biz_ids,
        firstResponseSeconds__isnull=False,
        createdAt__gte=prev_start, createdAt__lt=window_start
    )
    avg_curr = None
    avg_prev = None
    # try firstResponseSeconds first, fall back to entity avgResponseSeconds
    agg_curr = resp_qs_curr.aggregate(avg=Avg("firstResponseSeconds"))["avg"]
    if agg_curr is not None:
        avg_curr = round(agg_curr / 3600, 2)
    else:
        # fallback: avg of business avgResponseSeconds
        try:
            fb = biz_qs.aggregate(avg=Avg("avgResponseSeconds"))["avg"]
            avg_curr = round((fb or 0) / 3600, 2)
        except Exception:
            avg_curr = 0.0

    agg_prev = resp_qs_prev.aggregate(avg=Avg("firstResponseSeconds"))["avg"]
    avg_prev = round(agg_prev / 3600, 2) if agg_prev is not None else avg_curr

    resp_spark = []
    for i in range(window_days):
        ds = window_start + timedelta(days=i)
        de = ds + timedelta(days=1)
        agg = Conversation.objects.filter(
            business_id__in=biz_ids,
            firstResponseSeconds__isnull=False,
            createdAt__gte=ds, createdAt__lt=de
        ).aggregate(avg=Avg("firstResponseSeconds"))["avg"]
        resp_spark.append(round((agg or 0) / 3600, 2))

    # lower response time is better
    if avg_curr is not None and avg_prev is not None and avg_prev > 0:
        resp_pct = round((avg_curr - avg_prev) / avg_prev * 100)
        resp_delta = {"pct": resp_pct, "isImprovement": avg_curr <= avg_prev, "label": "faster" if avg_curr <= avg_prev else "slower"}
    elif avg_prev == 0:
        resp_delta = {"pct": None, "isImprovement": True, "label": "new"}
    else:
        resp_delta = {"pct": 0, "isImprovement": True}

    return {
        "enquiries": {
            "label": "Enquiries", "value": enq_curr, "unit": None,
            "delta": _delta(enq_curr, enq_prev), "sparkline": enq_spark,
        },
        "connections": {
            "label": "New Connections", "value": conn_curr, "unit": None,
            "delta": _delta(conn_curr, conn_prev), "sparkline": conn_spark,
        },
        "newListings": {
            "label": "New Listings", "value": list_curr, "unit": None,
            "delta": _delta(list_curr, list_prev), "sparkline": list_spark,
        },
        "avgResponseTime": {
            "label": "Avg Response Time", "value": avg_curr, "unit": "hrs",
            "delta": resp_delta, "sparkline": resp_spark,
        },
    }


# ---------------------------------------------------------------------------
# 7. Analytics chart
# ---------------------------------------------------------------------------
def analytics_chart(user, from_date, to_date, entity_type=None, object_id=None):
    from app_ib.models import BusinessAnalytics, Business
    from django.contrib.contenttypes.models import ContentType

    # determine scope
    if entity_type and object_id:
        # ownership check
        model = get_model(entity_type)
        obj = model.objects.filter(id=object_id).first()
        if not obj:
            raise NotFound_(f"{entity_type} not found")
        owner_id = _owner_id(obj)
        if owner_id != user.id:
            raise PermissionError_("not the owner")
        ct = content_type_for(entity_type)
        qs = BusinessAnalytics.objects.filter(contentType=ct, objectId=object_id)
    else:
        # all entities owned by the user: businesses
        biz_qs = Business.objects.filter(user=user)
        biz_ct = ContentType.objects.get_for_model(Business)
        biz_ids = list(biz_qs.values_list("id", flat=True))
        qs = BusinessAnalytics.objects.filter(contentType=biz_ct, objectId__in=biz_ids)

    qs = qs.filter(date__gte=from_date, date__lte=to_date)
    # group by date
    from django.db.models import Sum
    rows = (qs.values("date")
              .annotate(
                  v=Sum("viewCount"),
                  u=Sum("uniqueVisitorCount"),
                  l=Sum("leadCount"),
                  q=Sum("quoteCount"),
                  w=Sum("whatsappTapCount"),
                  c=Sum("callTapCount"),
                  s=Sum("saveCount"),
              ).order_by("date"))
    by_date = {r["date"]: r for r in rows}

    series = []
    d = from_date
    while d <= to_date:
        r = by_date.get(d, {})
        series.append({
            "date": d.isoformat(),
            "viewCount": r.get("v", 0) or 0,
            "uniqueVisitorCount": r.get("u", 0) or 0,
            "leadCount": r.get("l", 0) or 0,
            "quoteCount": r.get("q", 0) or 0,
            "whatsappTapCount": r.get("w", 0) or 0,
            "callTapCount": r.get("c", 0) or 0,
            "saveCount": r.get("s", 0) or 0,
        })
        d += timedelta(days=1)

    return {"from": from_date.isoformat(), "to": to_date.isoformat(), "series": series}


def _owner_id(obj):
    """Best-effort owner user id for ownership check."""
    uid = getattr(obj, "user_id", None)
    if uid:
        return uid
    biz = getattr(obj, "business", None)
    if biz:
        return getattr(biz, "user_id", None)
    return None


# ---------------------------------------------------------------------------
# 8. Shop / Architect public detail + lists
# ---------------------------------------------------------------------------
def _video_shape(v):
    return {
        "id": v.id,
        "videoUrl": v.videoUrl,
        "platformCode": v.platform.code if v.platform_id else "",
        "platformName": v.platform.name if v.platform_id else "",
        "isPrimary": v.isPrimary,
        "displayOrder": v.displayOrder,
        "createdAt": v.createdAt.isoformat(),
        "entityType": v.contentType.model if v.contentType_id else "",
        "objectId": v.objectId,
    }


def _shop_videos(shop):
    from app_ib.models import ShortVideoLink
    ct = content_type_for(ENTITY_TYPE.SHOP)
    return [_video_shape(v) for v in
            ShortVideoLink.objects.filter(contentType=ct, objectId=shop.id)
            .select_related("platform", "contentType")
            .order_by("-isPrimary", "displayOrder", "-createdAt")]


def _rating_breakdown(shop_or_arch):
    rb = getattr(shop_or_arch, "ratingBreakdown", {}) or {}
    return rb


def _segment_tags_for_shop(s, expertise=None):
    """Deterministic customer-segment tags derived from data the shop already
    provided at registration — no external calls, no extra model fields.
    """
    tags = []
    if expertise:
        tags.append(f"{expertise[0]} specialist")
    if s.city:
        tags.append(f"Serves {s.city}")
    business = s.business if s.business_id else None
    if business and business.isVerified:
        tags.append("IB Verified")
    if business and business.since:
        try:
            years = date.today().year - int(str(business.since).strip()[:4])
            if years >= 5:
                tags.append("Established")
        except (ValueError, TypeError):
            pass
    if business and business.products.filter(isActive=True).exists():
        tags.append("Products available")
    if business and business.services.filter(isActive=True).exists():
        tags.append("Services offered")
    if s.rating >= 4.5 and s.totalReviews >= 5:
        tags.append("Top rated")
    return tags


def _shop_full_dict(s, include_videos=True, include_details=True):
    d = {
        "id": s.id,
        "slug": s.slug,
        "name": s.name,
        "shopType": s.shopType,
        "bio": s.bio,
        "coverImage": s.coverImage,
        "bannerImage": s.bannerImage,
        "bannerLink": s.bannerLink,
        "city": s.city,
        "state": s.state,
        "lat": float(s.lat) if s.lat is not None else None,
        "lng": float(s.lng) if s.lng is not None else None,
        "rating": s.rating,
        "totalReviews": s.totalReviews,
        "ratingBreakdown": _rating_breakdown(s),
        "trendingScore": s.trendingScore,
        "hotScore": s.hotScore,
        "label": s.label,
        "viewCount": s.viewCount,
        "businessId": s.business_id,
        "businessName": s.business.businessName if s.business_id and s.business else None,
        "timestamp": s.timestamp.isoformat(),
    }
    if include_videos:
        d["videos"] = _shop_videos(s)
    if include_details:
        d["contacts"] = _contacts_for_shop(s)
        d["awards"] = _awards_for(s, "shop")
        d["credentials"] = _credentials_for(s, "shop")
        d["processSteps"] = _process_steps_for(s, "shop")
        d["expertise"] = _expertise_for(s)
        d["segmentTags"] = _segment_tags_for_shop(s, d["expertise"])
        d["updates"] = _shop_updates_for(s)
        d["qa"] = _shop_qa_for(s)
        # images = gallery rows + cover/banner fallback. Detail-only (like the
        # other relation-backed fields) — the list payload omits it to avoid an
        # extra per-row query in the async list path; the shop preview/popup
        # fetch the detail on select and get the full gallery there.
        d["images"] = _shop_images_for(s)
    return d


def get_shop(id_or_slug, user=None):
    from app_ib.models import Shop
    # try integer id first
    obj = None
    try:
        oid = int(id_or_slug)
        obj = Shop.objects.select_related("business").filter(id=oid).first()
    except (ValueError, TypeError):
        obj = Shop.objects.select_related("business").filter(slug=id_or_slug).first()

    if not obj:
        raise NotFound_("shop not found")
    if not obj.isActive and (user is None or not user.is_authenticated or obj.user_id != user.id):
        raise NotFound_("shop not found")
    return _shop_full_dict(obj, include_videos=True)


def get_shop_by_slug(slug, user=None):
    from app_ib.models import Shop
    obj = Shop.objects.select_related("business").filter(slug=slug).first()
    if not obj:
        raise NotFound_("shop not found")
    if not obj.isActive and (user is None or not user.is_authenticated or obj.user_id != user.id):
        raise NotFound_("shop not found")
    return _shop_full_dict(obj, include_videos=True)


def list_shops(city="", shop_type="", search="", sort="trending", page=1, page_size=20,
               category=""):
    from app_ib.models import Shop
    # prefetch_related("expertiseTags") is REQUIRED here: the list payload adds a
    # lightweight expertiseTags chip list per row below, and _expertise_for() reads
    # entity.expertiseTags.all() — without the prefetch that becomes a per-row query
    # inside this async list loop and 500s the endpoint (learned the hard way).
    qs = Shop.objects.select_related("business").prefetch_related("expertiseTags").filter(isActive=True)
    if city:
        qs = qs.filter(city__icontains=city)
    if shop_type:
        qs = qs.filter(shopType=shop_type)
    if category:
        # category chips map to expertiseTags (Tag slug) — see list_shop_categories
        qs = qs.filter(expertiseTags__slug=category).distinct()
    if search:
        qs = qs.filter(name__icontains=search)
    if sort == "rating":
        qs = qs.order_by("-rating", "-trendingScore")
    elif sort == "newest":
        qs = qs.order_by("-timestamp")
    else:
        qs = qs.order_by("-trendingScore", "-hotScore")

    page_size = min(int(page_size), 50)
    total = qs.count()
    offset = (int(page) - 1) * page_size
    items = []
    for s in qs[offset: offset + page_size]:
        d = _shop_full_dict(s, include_videos=False, include_details=False)
        # Reads the prefetched M2M cache only (no extra query) — capped at 3 chips.
        d["expertiseTags"] = _expertise_for(s)[:3]
        items.append(d)
    return {"items": items, "total": total, "page": int(page), "pageSize": page_size}


def _arch_projects(arch):
    from app_ib.models import Project
    return [{
        "id": p.id, "title": p.title, "slug": p.slug,
        "description": p.description, "coverImage": p.coverImage,
        "images": p.images, "city": p.city, "style": p.style, "tags": p.tags,
    } for p in Project.objects.filter(architect=arch, isActive=True).order_by("index", "-timestamp")]


def _arch_videos(arch):
    from app_ib.models import ShortVideoLink
    ct = content_type_for(ENTITY_TYPE.ARCHITECT)
    return [_video_shape(v) for v in
            ShortVideoLink.objects.filter(contentType=ct, objectId=arch.id)
            .select_related("platform", "contentType")
            .order_by("-isPrimary", "displayOrder", "-createdAt")]


def _contact_row(c):
    """Serialise a ContactInfo instance, omitting blank optional fields."""
    row = {
        "id": c.id,
        "label": c.label,
        "isPrimary": c.isPrimary,
        "countryCode": c.countryCode,
    }
    if c.phone:
        row["phone"] = c.phone
    if c.email:
        row["email"] = c.email
    if c.whatsapp:
        row["whatsapp"] = c.whatsapp
    if c.website:
        row["website"] = c.website
    if c.gmb:
        row["gmb"] = c.gmb
    if c.workingPlaceLink:
        row["mapsUrl"] = c.workingPlaceLink
    return row


def _contacts_for_architect(arch):
    from app_ib.engine_models import ContactInfo
    return [_contact_row(c) for c in ContactInfo.objects.filter(architect=arch).order_by("-isPrimary", "id")]


def _contacts_for_business(b):
    from app_ib.engine_models import ContactInfo
    return [_contact_row(c) for c in ContactInfo.objects.filter(business=b).order_by("-isPrimary", "id")]


def _contacts_for_shop(s):
    from app_ib.engine_models import ContactInfo
    return [_contact_row(c) for c in ContactInfo.objects.filter(shop=s).order_by("-isPrimary", "id")]


def _shop_updates_for(s):
    """Return active 'Shop update' cards for the shop (title/body/badge/color/date)."""
    return [
        {
            "title": u.title,
            "body": u.body,
            "badge": u.badge,
            "color": u.color,
            "date": u.timestamp.strftime("%d %b %Y") if u.timestamp else "",
        }
        for u in s.updates.filter(isActive=True).order_by("displayOrder", "-timestamp")
    ]


def _shop_images_for(s):
    """Return the shop gallery as a list of URL strings: active ShopImage rows
    (by index/timestamp) first, then coverImage + bannerImage appended if truthy
    and not already present. Deduped, order preserved; [] if nothing."""
    urls = [i.imageUrl for i in s.images.filter(isActive=True).order_by("index", "timestamp") if i.imageUrl]
    for extra in (s.coverImage, s.bannerImage):
        if extra and extra not in urls:
            urls.append(extra)
    return urls


def _shop_qa_for(s):
    """Return active customer Q&A entries for the shop (question/answer/askedBy/date)."""
    return [
        {
            "question": q.question,
            "answer": q.answer,
            "askedBy": q.askedBy,
            "date": q.timestamp.strftime("%d %b %Y") if q.timestamp else "",
        }
        for q in s.questions.filter(isActive=True).order_by("displayOrder", "-timestamp")
    ]


# ---------------------------------------------------------------------------
# Phase 1 — Award / ProcessStep / Expertise helpers
# ---------------------------------------------------------------------------

def _award_row(a):
    row = {
        "id": a.id,
        "title": a.title,
    }
    if a.issuer:
        row["issuer"] = a.issuer
    if a.year:
        row["year"] = a.year
    if a.description:
        row["description"] = a.description
    if a.imageUrl:
        row["imageUrl"] = a.imageUrl
    return row


def _awards_for(entity, fk):
    """Return award rows (kind='award') for the entity. fk = 'architect'|'shop'|'business'."""
    from app_ib.engine_models import Award
    return [_award_row(a) for a in
            Award.objects.filter(**{fk: entity, "kind": "award", "isActive": True})
            .order_by("index", "-timestamp")]


def _credentials_for(entity, fk):
    """Return credential title strings (kind='credential') for the entity."""
    from app_ib.engine_models import Award
    return [a.title for a in
            Award.objects.filter(**{fk: entity, "kind": "credential", "isActive": True})
            .order_by("index", "-timestamp")]


def _process_steps_for(entity, fk):
    """Return processStep rows for the entity."""
    from app_ib.engine_models import ProcessStep
    return [
        {
            "id": p.id,
            "stepNumber": p.stepNumber,
            "title": p.title,
            "description": p.description,
        }
        for p in ProcessStep.objects.filter(**{fk: entity, "isActive": True})
        .order_by("index", "-timestamp")
    ]


def _expertise_for(entity):
    """Return list of tag.value strings from the entity's expertiseTags M2M."""
    return [tag.value for tag in entity.expertiseTags.all()]


def _specialization_for(business):
    """AI-generated "what they specialize in" cards [{icon,title,desc}] (or [])."""
    spec = getattr(business, "specialization", None)
    return spec.cards if spec is not None else []


def _architect_pricing(a):
    """Summarise the architect's ArchitectPackage rows for the detail price card
    (task 108). Card shows a single line derived from the packages; the full list is
    returned too so a future multi-package UI needs no payload change.
    fromValue = cheapest active package; timeline/freeConsultation from the primary
    (lowest-index) active package. All None/""/[] when the architect has no packages."""
    pkgs = [p for p in a.packages.all() if p.isActive]
    if not pkgs:
        return {"fromValue": None, "freeConsultation": False, "typicalTimeline": "", "packages": []}
    priced = [p for p in pkgs if p.fromValue]
    from_value = min((p.fromValue for p in priced), default=None)
    primary = pkgs[0]  # Meta.ordering = index, id → lowest index first
    return {
        "fromValue": from_value,
        "freeConsultation": any(p.freeConsultation for p in pkgs),
        "typicalTimeline": primary.typicalTimeline or "",
        "packages": [{
            "title": p.title, "fromValue": p.fromValue, "typicalTimeline": p.typicalTimeline,
            "freeConsultation": p.freeConsultation, "description": p.description,
        } for p in pkgs],
    }


def _arch_full_dict(a, include_details=True, project_count=None):
    from app_ib.models import Project
    # use pre-annotated value when available (avoids N+1 in list view)
    if project_count is None:
        project_count = Project.objects.filter(architect=a).count()
    d = {
        "id": a.id,
        "slug": a.slug,
        "name": a.name,
        "bio": a.bio,
        "coverImage": a.coverImage,
        "city": a.city,
        "state": a.state,
        "rating": a.rating,
        "totalReviews": a.totalReviews,
        "ratingBreakdown": _rating_breakdown(a),
        "trendingScore": a.trendingScore,
        "label": a.label,
        "viewCount": a.viewCount,
        "projectCount": project_count,
        "timestamp": a.timestamp.isoformat(),
    }
    if include_details:
        d["projects"] = _arch_projects(a)
        d["businesses"] = [{"id": b.id, "name": b.businessName,
                             "slug": b.slug if hasattr(b, "slug") else ""}
                           for b in a.businesses.all()]
        d["videos"] = _arch_videos(a)
        d["contacts"] = _contacts_for_architect(a)
        d["awards"] = _awards_for(a, "architect")
        d["credentials"] = _credentials_for(a, "architect")
        d["processSteps"] = _process_steps_for(a, "architect")
        d["expertise"] = _expertise_for(a)
        d["pricing"] = _architect_pricing(a)  # task 108 price card
    return d


def get_architect(id_or_slug, user=None):
    from app_ib.models import Architect, Project
    obj = None
    try:
        oid = int(id_or_slug)
        obj = Architect.objects.prefetch_related("businesses").filter(id=oid).first()
    except (ValueError, TypeError):
        obj = Architect.objects.prefetch_related("businesses").filter(slug=id_or_slug).first()

    if not obj:
        raise NotFound_("architect not found")
    if not obj.isActive and (user is None or not user.is_authenticated or obj.user_id != user.id):
        raise NotFound_("architect not found")
    project_count = Project.objects.filter(architect=obj).count()
    return _arch_full_dict(obj, include_details=True, project_count=project_count)


def get_architect_by_slug(slug, user=None):
    from app_ib.models import Architect, Project
    obj = Architect.objects.prefetch_related("businesses").filter(slug=slug).first()
    if not obj:
        raise NotFound_("architect not found")
    if not obj.isActive and (user is None or not user.is_authenticated or obj.user_id != user.id):
        raise NotFound_("architect not found")
    project_count = Project.objects.filter(architect=obj).count()
    return _arch_full_dict(obj, include_details=True, project_count=project_count)


def list_architects(city="", search="", sort="trending", page=1, page_size=20, category=""):
    from app_ib.models import Architect, Project
    from django.db.models import Count as _Count
    qs = Architect.objects.filter(isActive=True)
    if city:
        qs = qs.filter(city__icontains=city)
    if category:
        # category chips map to expertiseTags (Tag slug) — see list_architect_categories
        qs = qs.filter(expertiseTags__slug=category).distinct()
    if search:
        qs = qs.filter(name__icontains=search)
    if sort == "rating":
        qs = qs.order_by("-rating", "-trendingScore")
    elif sort == "newest":
        qs = qs.order_by("-timestamp")
    else:
        qs = qs.order_by("-trendingScore", "-hotScore")

    page_size = min(int(page_size), 50)
    total = qs.count()
    offset = (int(page) - 1) * page_size
    # annotate project count to avoid N+1 (related_name on Project FK is "projects")
    page_qs = qs[offset: offset + page_size]
    page_qs = Architect.objects.filter(id__in=[a.id for a in page_qs]).annotate(
        _project_count=_Count("projects")
    )
    # preserve original ordering
    if sort == "rating":
        page_qs = page_qs.order_by("-rating", "-trendingScore")
    elif sort == "newest":
        page_qs = page_qs.order_by("-timestamp")
    else:
        page_qs = page_qs.order_by("-trendingScore", "-hotScore")
    items = [_arch_full_dict(a, include_details=False,
                             project_count=getattr(a, "_project_count", 0))
             for a in page_qs]
    return {"items": items, "total": total, "page": int(page), "pageSize": page_size}


# ---------------------------------------------------------------------------
# 8d. Public list endpoints: businesses / products / services / catalogues
#     Mirror of list_shops / list_architects (envelope, filtering, sort, pagination).
# ---------------------------------------------------------------------------
def _paginate(qs, page, page_size):
    """Shared offset pagination — returns (sliced_iterable, total, page, page_size)."""
    page_size = min(int(page_size), 50)
    total = qs.count()
    offset = (int(page) - 1) * page_size
    return qs[offset: offset + page_size], total, int(page), page_size


def _business_city(b):
    loc = getattr(b, "business_location", None)
    return loc.city if loc else ""


def _biz_full_dict(b):
    return {
        "id": b.id,
        "slug": b.slug,
        "name": b.businessName,
        "imageUrl": b.coverImageUrl or "",
        "rating": b.ratingValue,
        "ratingText": b.rating,
        "totalReviews": b.totalReviews,
        "trendingScore": b.trendingScore,
        "label": b.label or (b.businessType.lable if b.businessType_id and b.businessType else ""),
        "category": b.businessType.lable if b.businessType_id and b.businessType else "",
        "businessType": b.businessType.value if b.businessType_id and b.businessType else "",
        "companyName": b.brandName or b.businessName,
        "city": _business_city(b),
        "since": b.since or "",
        "isVerified": b.isVerified,
        "viewCount": b.viewCount,
        "timestamp": b.timestamp.isoformat(),
    }


def list_businesses(city="", business_type="", search="", sort="trending", page=1, page_size=20,
                    category="", verified=False, min_rating=None, min_years=None):
    from app_ib.models import Business
    qs = (Business.objects
          .select_related("businessType", "business_location")
          .filter(user__is_active=True))
    if city:
        qs = qs.filter(business_location__city__icontains=city)
    if min_rating:
        # businesses-mobile.html's "4.7★ & up" check — real field, no new column.
        qs = qs.filter(ratingValue__gte=min_rating)
    if min_years:
        # "10+ years in business". `since` is a free-text CharField, so only a plain
        # 4-digit year is comparable at all — and for fixed-width digit strings a
        # lexical <= IS the numeric <=. Rows with junk (or blank) `since` are excluded
        # rather than guessed at.
        import datetime
        cutoff = datetime.date.today().year - int(min_years)
        qs = qs.filter(since__regex=r"^\d{4}$", since__lte=str(cutoff))
    if business_type:
        qs = qs.filter(businessType__value=business_type)
    if category:
        # browse-by-room cards filter on the BusinessCategory M2M (value or lable)
        from django.db.models import Q
        qs = qs.filter(Q(businessCategory__value__iexact=category)
                       | Q(businessCategory__lable__iexact=category)).distinct()
    if verified:
        qs = qs.filter(isVerified=True)
    if search:
        # Broad text match: a query like "Modular Kitchens" is usually a
        # category/specialisation phrase, not a company name — matching only
        # businessName returned nothing (and killed every result when stacked
        # with ?category=). Match across name/brand/bio + the category/segment/
        # type taxonomy (value + lable) + expertise tags so search and category
        # stack instead of cancelling out.
        from django.db.models import Q
        qs = qs.filter(
            Q(businessName__icontains=search)
            | Q(brandName__icontains=search)
            | Q(bio__icontains=search)
            | Q(businessCategory__value__icontains=search)
            | Q(businessCategory__lable__icontains=search)
            | Q(businessSegment__value__icontains=search)
            | Q(businessSegment__lable__icontains=search)
            | Q(businessType__value__icontains=search)
            | Q(businessType__lable__icontains=search)
            | Q(expertiseTags__value__icontains=search)
        ).distinct()
    if sort == "rating":
        qs = qs.order_by("-ratingValue", "-trendingScore")
    elif sort == "newest":
        qs = qs.order_by("-timestamp")
    else:
        qs = qs.order_by("-trendingScore", "-hotScore")

    page_qs, total, page, page_size = _paginate(qs, page, page_size)
    items = [_biz_full_dict(b) for b in page_qs]
    return {"items": items, "total": total, "page": page, "pageSize": page_size}


def _first_image(related_manager):
    img = related_manager.order_by("index").first()
    return (img.image if img else "") or ""


def _price_bounds(qs):
    """Min/max displayPrice of the scope BEFORE price filtering — slider bounds."""
    from django.db.models import Min, Max
    agg = qs.aggregate(lo=Min("displayPrice"), hi=Max("displayPrice"))
    return {"min": float(agg["lo"] or 0), "max": float(agg["hi"] or 0)}


def _orig_price(o):
    """Reconstruct pre-discount price (the legacy displayPrice already has discount applied)."""
    try:
        if o.discountType == "amount":
            return float(o.displayPrice) + float(o.discountBy or 0)
        if o.discountType == "percent" and float(o.discountBy or 0) < 100:
            return float(o.displayPrice) / (1 - float(o.discountBy) / 100)
    except (ValueError, TypeError, ZeroDivisionError):
        pass
    return float(getattr(o, "orignalPrice", 0) or 0)


def _product_full_dict(p):
    return {
        "id": p.id,
        "slug": p.slug,
        "name": p.title,
        "imageUrl": _first_image(p.productImages),
        "rating": p.ratingValue,
        "totalReviews": p.totalReviews,
        "trendingScore": p.trendingScore,
        "label": p.label,
        # Category is what the card's eyebrow shows. Some products carry only a
        # sub-category, so fall back to it rather than sending "" and letting the
        # frontend print a generic "PRODUCT".
        "category": _product_category(p),
        "displayPrice": p.displayPrice,
        "orignalPrice": _orig_price(p),
        "discountType": p.discountType,
        "discountBy": p.discountBy,
        # Drives the card's attribute badge (in stock / made to order / sold out).
        # Nullable by design: no stock tracked = made to order.
        "stockQuantity": p.stockQuantity,
        "city": _business_city(p.business) if p.business_id else "",
        "businessName": p.business.businessName if p.business_id and p.business else "",
        # Drives the card's verified check-mark. The prototype shows it ONLY for a
        # verified seller, so the flag has to travel with the row (P2-43).
        "isVerified": bool(p.business.isVerified) if p.business_id and p.business else False,
        "viewCount": p.viewCount,
        "timestamp": p.updatedAt.isoformat(),
    }


def _product_category(p):
    """Real category label for a product: its category, else its sub-category, else ''."""
    cat = p.category.first()
    if cat is not None:
        return cat.lable
    sub = p.subCategory.first()
    return sub.lable if sub is not None else ""


def _service_category(s):
    """Real category label for a service (same rule as products)."""
    cat = s.category.first()
    if cat is not None:
        return cat.lable
    sub = s.subCategory.first()
    return sub.lable if sub is not None else ""


def list_products(city="", category="", search="", sort="trending", page=1, page_size=20,
                  min_price=None, max_price=None, verified=False, in_stock=False,
                  rating_min=None):
    from django.db.models import Q
    from interior_products.models import Product
    qs = (Product.objects
          .select_related("business", "business__business_location")
          .filter(isActive=True))
    if city:
        qs = qs.filter(business__business_location__city__icontains=city)
    if category:
        qs = qs.filter(category__value=category).distinct()
    if search:
        qs = qs.filter(title__icontains=search)
    if verified:
        qs = qs.filter(business__isVerified=True)
    if in_stock:
        # null stockQuantity = untracked → counts as in stock (same rule as detail page)
        qs = qs.filter(Q(stockQuantity__isnull=True) | Q(stockQuantity__gt=0))
    if rating_min is not None:
        qs = qs.filter(ratingValue__gte=rating_min)
    price_range = _price_bounds(qs)
    if min_price is not None:
        qs = qs.filter(displayPrice__gte=min_price)
    if max_price is not None:
        qs = qs.filter(displayPrice__lte=max_price)
    if sort == "rating":
        qs = qs.order_by("-ratingValue", "-trendingScore")
    elif sort == "newest":
        qs = qs.order_by("-updatedAt")
    elif sort == "price-low":
        qs = qs.order_by("displayPrice", "-trendingScore")
    elif sort == "price-high":
        qs = qs.order_by("-displayPrice", "-trendingScore")
    else:
        qs = qs.order_by("-trendingScore", "-hotScore")

    page_qs, total, page, page_size = _paginate(qs, page, page_size)
    items = [_product_full_dict(p) for p in page_qs]
    return {"items": items, "total": total, "page": page, "pageSize": page_size,
            "priceRange": price_range}


def list_product_categories():
    """Product category taxonomy for the products filter sidebar.

    Returns active categories (in editor `index` order) with the count of
    active products in each, so the sidebar can both label and size the filter.
    `value` is exactly what list_products filters on (category__value), so the
    frontend uses it as the option id. Categories with no active products are
    omitted to keep the filter list meaningful."""
    from django.db.models import Count, Q
    from interior_products.models import ProductCategory
    cats = (ProductCategory.productOnes()
            .annotate(productCount=Count(
                "catProducts", filter=Q(catProducts__isActive=True), distinct=True))
            .filter(productCount__gt=0)
            .order_by("index", "id"))
    return [{"value": c.value, "label": c.lable, "count": c.productCount} for c in cats]


def list_service_categories():
    """Service category taxonomy for the services filter bar.

    Service categories live in the ProductCategory table (Service.category M2M
    -> ProductCategory, related_name 'catServices') but are a SEPARATE
    taxonomy, marked by the `svc-` value prefix — Furniture is a product
    category and must never reach this chip row. Returns active service
    categories (editor `index` order) with the count of active services in
    each. `value` is what list_services filters on (category__value);
    categories with no active services are omitted so the chip list stays
    meaningful."""
    from django.db.models import Count, Q
    from interior_products.models import ProductCategory
    cats = (ProductCategory.serviceOnes()
            .annotate(serviceCount=Count(
                "catServices", filter=Q(catServices__isActive=True), distinct=True))
            .filter(serviceCount__gt=0)
            .order_by("index", "id"))
    return [{"value": c.value, "label": c.lable, "count": c.serviceCount} for c in cats]


def list_business_categories():
    """Business category taxonomy for the businesses filter bar.

    Categories come from the BusinessCategory M2M (businessCategory). Returns
    categories (editor `index` order) with the count of businesses (active
    user) in each. `value` is what list_businesses filters on (matched against
    businessCategory value or lable); empty categories are omitted."""
    from django.db.models import Count, Q
    from app_ib.models import BusinessCategory
    cats = (BusinessCategory.objects.filter(isActive=True)
            .annotate(bizCount=Count(
                "business_category", filter=Q(business_category__user__is_active=True), distinct=True))
            .filter(bizCount__gt=0)
            .order_by("index", "id"))
    return [{"value": c.value, "label": c.lable, "count": c.bizCount} for c in cats]


def list_shop_categories():
    """Shop category taxonomy for the shops filter bar.

    Categories come from shop expertiseTags (Tag, related_name
    'expert_shops'). Returns tags used by at least one active shop, most-used
    first. `value` is the Tag slug, which list_shops filters on
    (expertiseTags__slug)."""
    from django.db.models import Count, Q
    from app_ib.engine_models import Tag
    tags = (Tag.objects
            .annotate(shopCount=Count(
                "expert_shops", filter=Q(expert_shops__isActive=True), distinct=True))
            .filter(shopCount__gt=0)
            .order_by("-shopCount", "value"))
    return [{"value": t.slug, "label": t.value, "count": t.shopCount} for t in tags]


def list_architect_categories():
    """Architect specialization taxonomy for the architects filter bar.

    Categories come from architect expertiseTags (Tag, related_name
    'expert_architects'). Returns tags used by at least one active architect,
    most-used first. `value` is the Tag slug, which list_architects filters on
    (expertiseTags__slug)."""
    from django.db.models import Count, Q
    from app_ib.engine_models import Tag
    tags = (Tag.objects
            .annotate(archCount=Count(
                "expert_architects", filter=Q(expert_architects__isActive=True), distinct=True))
            .filter(archCount__gt=0)
            .order_by("-archCount", "value"))
    return [{"value": t.slug, "label": t.value, "count": t.archCount} for t in tags]


def _service_full_dict(s):
    return {
        "id": s.id,
        "slug": s.slug,
        "name": s.title,
        "imageUrl": _first_image(s.serviceImages),
        "rating": s.ratingValue,
        "totalReviews": s.totalReviews,
        "trendingScore": s.trendingScore,
        "label": s.label,
        # Same fallback as products: a service with only a sub-category still has a
        # real eyebrow instead of an empty one.
        "category": _service_category(s),
        "serviceTags": _parse_tag_list(s.serviceTags),
        "displayPrice": s.displayPrice,
        "orignalPrice": _orig_price(s),
        "discountType": s.discountType,
        "discountBy": s.discountBy,
        # Services have no stock — the owner flips availability. This is what the
        # card's attribute badge shows ("Accepting work" / "Not available").
        "isAvailable": s.isAvailable,
        # Seller-stated turnaround in days — the card's pill (P3-26). null = not
        # stated, and the pill does NOT render. Never derived: fabricating a
        # delivery promise from tags/title is worse than no pill.
        "turnaroundDays": s.turnaroundDays,
        # The provider's IB-verified state. The card's rosette is a TRUST CLAIM, so
        # it must be gated on this — it was rendered unconditionally because the
        # payload had no field to gate on (P3-17). Same shape as _product_full_dict.
        "isVerified": bool(s.business.isVerified) if s.business_id and s.business else False,
        "city": _business_city(s.business) if s.business_id else "",
        "businessName": s.business.businessName if s.business_id and s.business else "",
        "viewCount": s.viewCount,
        "timestamp": s.updatedAt.isoformat(),
    }


def list_services(city="", category="", search="", sort="trending", page=1, page_size=20,
                  min_price=None, max_price=None, verified=False, rating_min=None,
                  available=False, free_consult=False):
    from interior_products.models import Service
    qs = (Service.objects
          .select_related("business", "business__business_location")
          .filter(isActive=True))
    if city:
        qs = qs.filter(business__business_location__city__icontains=city)
    if category:
        qs = qs.filter(category__value=category).distinct()
    if search:
        qs = qs.filter(title__icontains=search)
    if verified:
        qs = qs.filter(business__isVerified=True)
    # "Open today" — the owner-controlled accepting-work switch (services have no
    # stock). The sheet's checkbox filters on the field that already exists.
    if available:
        qs = qs.filter(isAvailable=True)
    # "Free consultation" — there is no such field on Service and a schema change
    # is out of scope, so it is DERIVED from the service's own text, the same way
    # catalogue_kind() is. Nothing is invented: a service only matches if it says
    # so itself, in its tags, title or description.
    if free_consult:
        qs = qs.filter(Q(serviceTags__icontains="free consult")
                       | Q(title__icontains="free consult")
                       | Q(description__icontains="free consult"))
    if rating_min is not None:
        qs = qs.filter(ratingValue__gte=rating_min)
    price_range = _price_bounds(qs)
    if min_price is not None:
        qs = qs.filter(displayPrice__gte=min_price)
    if max_price is not None:
        qs = qs.filter(displayPrice__lte=max_price)
    if sort == "rating":
        qs = qs.order_by("-ratingValue", "-trendingScore")
    elif sort == "newest":
        qs = qs.order_by("-updatedAt")
    elif sort == "price-low":
        qs = qs.order_by("displayPrice", "-trendingScore")
    elif sort == "price-high":
        qs = qs.order_by("-displayPrice", "-trendingScore")
    else:
        qs = qs.order_by("-trendingScore", "-hotScore")

    page_qs, total, page, page_size = _paginate(qs, page, page_size)
    items = [_service_full_dict(s) for s in page_qs]
    return {"items": items, "total": total, "page": page, "pageSize": page_size,
            "priceRange": price_range}


def _catalogue_full_dict(c):
    return {
        "id": c.id,
        "slug": c.slug,
        "name": c.title,
        "imageUrl": c.catelougeImage or "",
        "pdfUrl": c.catelougePdf or "",
        "ytLink": c.ytLink or "",
        "downloads": c.totalDownload,
        "rating": 0.0,
        "totalReviews": 0,
        "trendingScore": c.trendingScore,
        "label": c.label,
        "category": (c.category
                     or (c.catelogueType.lable if c.catelogueType_id and c.catelogueType else "")),
        "catalogueType": c.catelogueType.value if c.catelogueType_id and c.catelogueType else "",
        # The catalogue's KIND — what the card's eyebrow shows and what the filter
        # chips select on. Derived (see catalogue_kind); no schema change.
        "kind": catalogue_kind(c),
        "kindLabel": CATALOGUE_KIND_LABEL[catalogue_kind(c)],
        "city": _business_city(c.business) if c.business_id else "",
        "businessId": c.business_id,
        "businessName": c.business.businessName if c.business_id and c.business else "",
        "viewCount": c.viewCount,
        "timestamp": c.createdAt.isoformat(),
    }


def catalogue_kind(c):
    """The catalogue's KIND — brand catalogue / project portfolio / editor pick.

    There is no kind field on the model (Catelogue.catelogueType is a BusinessType:
    Interior/Sanitary), so it is DERIVED from what the catalogue actually is:
    an editor pick is labelled as one; a portfolio/lookbook says so in its title;
    anything else is a business's own brand catalogue. Nothing is invented — the
    signal is the catalogue's own text."""
    label = (c.label or "").lower()
    if "editor" in label or "pick" in label:
        return "editor"
    text = f"{c.title or ''} {c.description or ''}".lower()
    if any(w in text for w in ("portfolio", "lookbook", "project")):
        return "portfolio"
    return "brand"


CATALOGUE_KIND_LABEL = {
    "brand": "Brand catalogue",
    "portfolio": "Project portfolio",
    "editor": "Editor pick",
}

# The frontend's chip ids for the same three kinds (catalogues.content.ts).
CATALOGUE_KIND_ALIAS = {
    "project": "portfolio",
    "collection": "editor",
    "portfolio": "portfolio",
    "editor": "editor",
    "brand": "brand",
}

# The same rules as catalogue_kind(), expressed as querysets so the filter chips
# ("Brand catalogues" / "Project portfolios" / "IB Editor picks") actually return
# results instead of always being empty.
def _filter_catalogue_kind(qs, kind):
    from django.db.models import Q
    editor_q = Q(label__icontains="editor") | Q(label__icontains="pick")
    portfolio_q = (Q(title__icontains="portfolio") | Q(description__icontains="portfolio")
                   | Q(title__icontains="lookbook") | Q(description__icontains="lookbook")
                   | Q(title__icontains="project") | Q(description__icontains="project"))
    if kind == "editor":
        return qs.filter(editor_q)
    if kind == "portfolio":
        return qs.filter(portfolio_q).exclude(editor_q)
    if kind == "brand":
        return qs.exclude(editor_q).exclude(portfolio_q)
    return qs


def list_catalogues(city="", category="", search="", sort="trending", page=1, page_size=20,
                    verified=False, year=None, free=False):
    from interior_products.models import Catelogue
    qs = (Catelogue.objects
          .select_related("business", "business__business_location", "catelogueType")
          .filter(isActive=True))
    if city:
        qs = qs.filter(business__business_location__city__icontains=city)
    if category:
        # The chip ids ARE catalogue kinds (brand/portfolio/editor). They used to be
        # matched against catelogueType__value, which only ever holds "Interior" /
        # "Sanitary" — so every one of those chips returned ZERO results (P6-18).
        kind = CATALOGUE_KIND_ALIAS.get(category)
        if kind:
            qs = _filter_catalogue_kind(qs, kind)
        else:
            qs = qs.filter(catelogueType__value=category)
    if search:
        qs = qs.filter(title__icontains=search)
    if verified:
        qs = qs.filter(business__isVerified=True)
    # "2026 releases" facet — filter by publish year (not a catelogueType).
    if year:
        qs = qs.filter(createdAt__year=year)
    # "Free downloads" facet — catalogues with a downloadable PDF (all are free).
    if free:
        qs = qs.exclude(catelougePdf="").exclude(catelougePdf__isnull=True)
    if sort == "rating":
        qs = qs.order_by("-trendingScore", "-totalDownload")
    elif sort == "newest":
        qs = qs.order_by("-createdAt")
    elif sort == "downloads":
        qs = qs.order_by("-totalDownload", "-trendingScore")
    else:
        qs = qs.order_by("-trendingScore", "-hotScore")

    page_qs, total, page, page_size = _paginate(qs, page, page_size)
    items = [_catalogue_full_dict(c) for c in page_qs]
    return {"items": items, "total": total, "page": page, "pageSize": page_size}


def _catalogue_images(c):
    """catelogueImages ordered by index; fall back to the catalogue's own cover image."""
    imgs = [{"id": im.id, "imageUrl": im.catelougeImage, "index": im.index, "link": im.link or ""}
            for im in c.catelogueImages.all().order_by("index")]
    if imgs:
        return imgs
    return [{"id": None, "imageUrl": c.catelougeImage or "", "index": 1, "link": ""}]


def _catalogue_business_dict(b):
    """Compact company card for the catalogue detail panel (mirrors productsV3Controller)."""
    if not b:
        return None
    loc = getattr(b, "business_location", None)
    prof = getattr(b, "business_profile", None)
    user_profile = getattr(b.user, "user_profile", None) if b.user_id else None
    return {
        "id": b.id,
        "name": b.businessName,
        "slug": b.slug,
        "businessType": b.businessType.lable if b.businessType_id and b.businessType else "",
        "city": loc.city if loc else "",
        "state": loc.locationState.name if loc and loc.locationState_id and loc.locationState else "",
        "isVerified": b.isVerified,
        "ratingValue": b.ratingValue,
        "totalReviews": b.totalReviews,
        "coverImageUrl": b.coverImageUrl or "",
        "since": b.since or "",
        "gst": b.gst or "",
        "phone": user_profile.phone if user_profile and user_profile.phone else "",
        "countryCode": user_profile.countryCode if user_profile and user_profile.countryCode else "",
        "about": (prof.about if prof and prof.about else "") or (b.bio or ""),
        "catalogueCount": b.catelogues.filter(isActive=True).count(),
    }


def _similar_catalogues(c, limit=5):
    from interior_products.models import Catelogue
    base = (Catelogue.objects
            .select_related("business", "business__business_location", "catelogueType")
            .filter(isActive=True).exclude(id=c.id))
    rows = []
    if c.catelogueType_id:
        rows = list(base.filter(catelogueType_id=c.catelogueType_id).order_by("-trendingScore")[:limit])
    if not rows and c.category:
        rows = list(base.filter(category=c.category).order_by("-trendingScore")[:limit])
    return [_catalogue_full_dict(x) for x in rows]


def catalogue_detail(slug_or_id):
    """Full detail payload for the /catalogues page detail panel — id or slug lookup."""
    from interior_products.models import Catelogue
    qs = (Catelogue.objects
          .select_related("business", "business__businessType", "business__business_location",
                           "business__business_location__locationState", "business__user",
                           "business__user__user_profile", "business__business_profile",
                           "catelogueType")
          .prefetch_related("catelogueImages"))
    value = str(slug_or_id)
    obj = qs.filter(id=int(value)).first() if value.isdigit() else qs.filter(slug=value).first()
    if not obj or not obj.isActive:
        raise NotFound_("catalogue not found")

    data = _catalogue_full_dict(obj)
    data["description"] = obj.description or ""
    data["specifications"] = obj.specifications or {}
    data["images"] = _catalogue_images(obj)
    data["business"] = _catalogue_business_dict(obj.business) if obj.business_id else None
    data["similar"] = _similar_catalogues(obj)
    return data


# ---------------------------------------------------------------------------
# 8e. Business public detail (core + related offerings + review summary)
#     Mirror of get_shop / get_architect — direct ORM, no Redis cache needed.
# ---------------------------------------------------------------------------
def _business_images(b):
    """Gallery image URLs for a business: profile primary/secondary + cover/banner."""
    urls = []
    prof = getattr(b, "business_profile", None)
    if prof:
        if prof.primaryImageUrl:
            urls.append(prof.primaryImageUrl)
        # secondaryImagesUrl is a comma/newline separated TextField in legacy data
        for chunk in (prof.secondaryImagesUrl or "").replace("\n", ",").split(","):
            chunk = chunk.strip()
            if chunk:
                urls.append(chunk)
    if b.coverImageUrl and b.coverImageUrl not in urls:
        urls.append(b.coverImageUrl)
    if b.bannerImageUrl and b.bannerImageUrl not in urls:
        urls.append(b.bannerImageUrl)
    return urls


def _primary_contact_field(b, field):
    """Value of `field` on the business's primary ContactInfo row ("" when none)."""
    c = b.contacts.order_by("-isPrimary", "id").first()
    return getattr(c, field, "") or "" if c else ""


def _business_social_links(b):
    out = []
    for sm in b.businessSocialMedia.select_related("socialMedia").all():
        out.append({
            "name": sm.socialMedia.name if sm.socialMedia_id else "",
            "link": sm.link or "",
        })
    return out


def _business_schedule(b):
    day_names = {1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday",
                 5: "Friday", 6: "Saturday", 7: "Sunday"}
    out = []
    for d in b.schedules.all().order_by("day"):
        out.append({
            "day": day_names.get(d.day, ""),
            "dayCode": d.day,
            "startTime": d.startTime.strftime("%H:%M") if d.startTime else "",
            "endTime": d.endTime.strftime("%H:%M") if d.endTime else "",
            "isWorking": d.isWorking,
        })
    return out


def _business_review_summary(b):
    """Lean rating summary (average/count + star breakdown) for the detail payload.

    The recent-reviews LIST is intentionally NOT fetched here — it was the slow
    part of the business detail call (a select_related scan per request). The v3
    detail page now lazy-loads the written reviews separately via
    GET reviews/?entityType=business&objectId=, so the main payload stays light.
    `recent` is kept as an empty list to preserve the response shape."""
    return {
        "average": b.ratingValue,
        "count": b.totalReviews,
        "ratingText": b.rating or "",
        "ratingBreakdown": _rating_breakdown(b),
        "recent": [],
    }


def _business_products(b, limit=12):
    from interior_products.models import Product
    qs = (Product.objects
          .filter(business_id=b.id, isActive=True)
          .prefetch_related("productImages")
          .order_by("index", "-trendingScore"))[:limit]
    return [_product_full_dict(p) for p in qs]


def _business_services(b, limit=12):
    from interior_products.models import Service
    qs = (Service.objects
          .filter(business_id=b.id, isActive=True)
          .prefetch_related("serviceImages")
          .order_by("index", "-trendingScore"))[:limit]
    return [_service_full_dict(s) for s in qs]


def _business_catalogues(b, limit=12):
    from interior_products.models import Catelogue
    qs = (Catelogue.objects
          .select_related("catelogueType")
          .filter(business_id=b.id, isActive=True)
          .order_by("index", "-trendingScore"))[:limit]
    return [_catalogue_full_dict(c) for c in qs]


def _business_projects(b, limit=12):
    from app_ib.engine_models import Project
    qs = (Project.objects
          .filter(business=b, isActive=True)
          .order_by("index", "-timestamp"))[:limit]
    return [{
        "id": p.id, "title": p.title, "slug": p.slug,
        "description": p.description, "coverImage": p.coverImage,
        "images": p.images, "city": p.city, "style": p.style, "tags": p.tags,
    } for p in qs]


def _business_full_dict(b):
    loc = getattr(b, "business_location", None)
    prof = getattr(b, "business_profile", None)
    segments = [s.lable for s in b.businessSegment.all()]
    categories = [c.lable for c in b.businessCategory.all()]
    return {
        # --- core identity ---
        "id": b.id,
        "slug": b.slug,
        "name": b.businessName,
        "companyName": b.brandName or b.businessName,
        "bio": b.bio or "",
        "about": (prof.about if prof and prof.about else "") or (b.bio or ""),
        "youtubeLink": prof.youtubeLink if prof and prof.youtubeLink else "",
        "imageUrls": _business_images(b),
        "coverImageUrl": b.coverImageUrl or "",
        "bannerImageUrl": b.bannerImageUrl or "",
        "bannerLink": b.bannerLink or "",
        "bannerText": b.bannerText or "",
        # --- ratings ---
        "rating": b.ratingValue,
        "ratingValue": b.ratingValue,
        "ratingText": b.rating or "",
        "totalReviews": b.totalReviews,
        "ratingBreakdown": _rating_breakdown(b),
        # --- classification ---
        "category": b.businessType.lable if b.businessType_id and b.businessType else "",
        "businessType": b.businessType.value if b.businessType_id and b.businessType else "",
        "segments": segments,
        "categories": categories,
        "label": b.label or (b.businessType.lable if b.businessType_id and b.businessType else ""),
        # --- location ---
        "city": loc.city if loc else "",
        "pinCode": loc.pinCode if loc else "",
        "state": (loc.locationState.name if loc and loc.locationState_id and loc.locationState else "") if loc else "",
        "country": (loc.locationCountry.name if loc and loc.locationCountry_id and loc.locationCountry else "") if loc else "",
        "locationLink": loc.locationLink if loc else "",
        # --- contact / CTA ---
        "whatsapp": b.whatsapp or "",
        "gst": b.gst or "",
        "socialLinks": _business_social_links(b),
        # F1: the wizard's own contact fields, read back off the primary contact row
        # (the `contacts` list below is the multi-row view of the same data).
        "publicEmail": _primary_contact_field(b, "email"),
        "website": _primary_contact_field(b, "website"),
        # F1: wizard step-2 keywords (same store as the Autogrowth tab).
        "serviceKeywords": [k.term for k in b.autogrowth_keywords.all()],
        # --- meta ---
        "since": b.since or "",
        # F1 (2026-07-16): profile-wizard fields the seller edits + we now persist.
        "brandName": b.brandName or "",
        "cin": b.cin or "",
        "pan": b.pan or "",
        "udyam": b.udyam or "",
        "founderName": b.founderName or "",
        "teamSize": b.teamSize or "",
        "businessModel": b.businessModel or "",
        "productPriceTiers": b.productPriceTiers or [],
        "isVerified": b.isVerified,
        # F2: publish state. isActive doubles as the soft-delete flag — there is no
        # separate publish column — so `isActive` IS "is this profile live".
        "isActive": b.isActive,
        "canGoLive": b.canGoLive,
        "completionPercent": b.completionPercent,
        "viewCount": b.viewCount,
        "trendingScore": b.trendingScore,
        # Already on the model and already used by product/service detail to derive
        # "Responds within N hrs" — it just never reached the business payload (P9-4).
        "avgResponseSeconds": b.avgResponseSeconds,
        # Trust/quality fields added 2026-07-15 (user-approved). null/false → the
        # KPI cell / credential chip is omitted (P9-20).
        "avgProjectValue": b.avgProjectValue,
        "coaRegistered": b.coaRegistered,
        "liabilityInsured": b.liabilityInsured,
        "schedule": _business_schedule(b),
        "timestamp": b.timestamp.isoformat(),
        # --- badge ---
        "businessBadge": {"type": b.businessBadge.type, "imageUrl": b.businessBadge.imageUrl or ""}
                         if b.businessBadge_id and b.businessBadge else None,
        # --- related collections ---
        "products": _business_products(b),
        "services": _business_services(b),
        "catalogues": _business_catalogues(b),
        "projects": _business_projects(b),
        "contacts": _contacts_for_business(b),
        # --- credentials / process / expertise (Phase 1) ---
        "awards": _awards_for(b, "business"),
        "credentials": _credentials_for(b, "business"),
        "processSteps": _process_steps_for(b, "business"),
        "expertise": _expertise_for(b),
        "specialization": _specialization_for(b),
        # --- review summary ---
        "reviewSummary": _business_review_summary(b),
    }


def _get_business_qs():
    from app_ib.models import Business
    return (Business.objects
            .select_related("businessType", "businessBadge",
                            "business_location", "business_location__locationState",
                            "business_location__locationCountry", "business_profile",
                            "specialization")
            .prefetch_related("businessSegment", "businessCategory",
                              "businessSocialMedia__socialMedia", "schedules",
                              "autogrowth_keywords", "contacts"))


def get_business(id_or_slug, user=None):
    obj = None
    try:
        oid = int(id_or_slug)
        obj = _get_business_qs().filter(id=oid).first()
    except (ValueError, TypeError):
        obj = _get_business_qs().filter(slug=id_or_slug).first()
    if not obj:
        raise NotFound_("business not found")
    # Soft-deleted business is hidden from everyone except its owner (mirrors shop/architect).
    if not obj.isActive and (user is None or not user.is_authenticated or obj.user_id != user.id):
        raise NotFound_("business not found")
    return _business_full_dict(obj)


def get_business_by_slug(slug, user=None):
    obj = _get_business_qs().filter(slug=slug).first()
    if not obj:
        raise NotFound_("business not found")
    if not obj.isActive and (user is None or not user.is_authenticated or obj.user_id != user.id):
        raise NotFound_("business not found")
    return _business_full_dict(obj)


# ---------------------------------------------------------------------------
# 8e-bis. Per-business offering lists (paginated) — the dedicated Products /
#         Services / Catalogue tabs on the v3 detail page fetch these lazily
#         instead of relying on the small preview embedded in the detail payload.
#         Item shape matches the catalog list endpoints (same *_full_dict), so
#         the frontend reuses the same mappers.
# ---------------------------------------------------------------------------
def get_business_products(business_id, page=1, page_size=20):
    from interior_products.models import Product
    qs = (Product.objects
          .select_related("business", "business__business_location")
          .prefetch_related("productImages")
          .filter(business_id=business_id, isActive=True)
          .order_by("index", "-trendingScore"))
    page_qs, total, page, page_size = _paginate(qs, page, page_size)
    return {"items": [_product_full_dict(p) for p in page_qs],
            "total": total, "page": page, "pageSize": page_size}


def get_business_services(business_id, page=1, page_size=20):
    from interior_products.models import Service
    qs = (Service.objects
          .select_related("business", "business__business_location")
          .prefetch_related("serviceImages")
          .filter(business_id=business_id, isActive=True)
          .order_by("index", "-trendingScore"))
    page_qs, total, page, page_size = _paginate(qs, page, page_size)
    return {"items": [_service_full_dict(s) for s in page_qs],
            "total": total, "page": page, "pageSize": page_size}


def get_business_catalogues(business_id, page=1, page_size=20):
    from interior_products.models import Catelogue
    qs = (Catelogue.objects
          .select_related("catelogueType", "business", "business__business_location")
          .filter(business_id=business_id, isActive=True)
          .order_by("index", "-trendingScore"))
    page_qs, total, page, page_size = _paginate(qs, page, page_size)
    return {"items": [_catalogue_full_dict(c) for c in page_qs],
            "total": total, "page": page, "pageSize": page_size}


# ---------------------------------------------------------------------------
# 9. Video CRUD
# ---------------------------------------------------------------------------
def _video_entity_owner(entity_type, object_id, user_id):
    """Return True if user_id owns the entity."""
    try:
        model = get_model(entity_type)
        obj = model.objects.filter(id=object_id).first()
        if not obj:
            return False
        owner = _owner_id(obj)
        return owner == user_id
    except Exception:
        return False


def list_videos(entity_type, object_id):
    from app_ib.models import ShortVideoLink
    ct = content_type_for(entity_type)
    return [_video_shape(v) for v in
            ShortVideoLink.objects.filter(contentType=ct, objectId=object_id)
            .select_related("platform", "contentType")
            .order_by("-isPrimary", "displayOrder", "-createdAt")]


def create_video(user, entity_type, object_id, payload):
    from app_ib.models import ShortVideoLink, Platform
    if not _video_entity_owner(entity_type, object_id, user.id):
        raise PermissionError_("not the entity owner")
    ct = content_type_for(entity_type)
    platform = None
    code = payload.get("platformCode", "")
    if code:
        platform = Platform.objects.filter(code=code).first()
    v = ShortVideoLink.objects.create(
        contentType=ct, objectId=object_id,
        videoUrl=payload.get("videoUrl", ""),
        platform=platform,
        isPrimary=bool(payload.get("isPrimary", False)),
        displayOrder=int(payload.get("displayOrder", 0)),
    )
    return _video_shape(v)


def update_video(user, video_id, payload):
    from app_ib.models import ShortVideoLink, Platform
    v = ShortVideoLink.objects.select_related("contentType").filter(id=video_id).first()
    if not v:
        raise NotFound_("video not found")
    et = v.contentType.model if v.contentType_id else ""
    if not _video_entity_owner(et, v.objectId, user.id):
        raise PermissionError_("not the entity owner")
    if "videoUrl" in payload:
        v.videoUrl = payload["videoUrl"]
    if "platformCode" in payload:
        from app_ib.models import Platform
        v.platform = Platform.objects.filter(code=payload["platformCode"]).first()
    if "isPrimary" in payload:
        v.isPrimary = bool(payload["isPrimary"])
    if "displayOrder" in payload:
        v.displayOrder = int(payload["displayOrder"])
    v.save()
    return _video_shape(v)


def delete_video(user, video_id):
    from app_ib.models import ShortVideoLink
    v = ShortVideoLink.objects.select_related("contentType").filter(id=video_id).first()
    if not v:
        raise NotFound_("video not found")
    et = v.contentType.model if v.contentType_id else ""
    if not _video_entity_owner(et, v.objectId, user.id):
        raise PermissionError_("not the entity owner")
    v.delete()
    return True


def set_primary_video(user, video_id):
    from app_ib.models import ShortVideoLink
    v = ShortVideoLink.objects.select_related("contentType").filter(id=video_id).first()
    if not v:
        raise NotFound_("video not found")
    et = v.contentType.model if v.contentType_id else ""
    if not _video_entity_owner(et, v.objectId, user.id):
        raise PermissionError_("not the entity owner")
    # clear siblings
    ShortVideoLink.objects.filter(contentType=v.contentType, objectId=v.objectId).update(isPrimary=False)
    v.isPrimary = True
    v.save(update_fields=["isPrimary"])
    return _video_shape(v)


# ---------------------------------------------------------------------------
# 10. Leads
# ---------------------------------------------------------------------------
def prioritized_leads(user, business_id=None):
    from app_ib.models import Business, LeadQuery
    from app_ib.algorithms.ranking import prioritize_leads

    if business_id:
        biz = Business.objects.filter(id=business_id).first()
        if not biz:
            raise NotFound_("business not found")
        if biz.user_id != user.id:
            raise PermissionError_("not your business")
    else:
        biz = Business.objects.filter(user=user).first()
        if not biz:
            raise NotFound_("no business found for user")

    scored = prioritize_leads(biz)
    # enrich with display fields
    lead_ids = [s["lead_id"] for s in scored]
    leads_map = {l.id: l for l in LeadQuery.objects.filter(id__in=lead_ids)}
    out = []
    for s in scored:
        lead = leads_map.get(s["lead_id"])
        if not lead:
            continue
        out.append({
            "leadId": lead.id,
            "score": s["score"],
            "factors": s["factors"],
            "why": s["why"],
            "name": lead.name or "",
            "phone": lead.phone or "",
            "email": lead.email or "",
            "city": lead.city or "",
            "interested": lead.interested or "",
            "status": lead.status or "",
            "leadStatus": lead.leadStatus or "",
            "stage": lead.stage or "",
            "messageCount": lead.messageCount or 0,
            "createdAt": lead.timestamp.isoformat(),
            # Seller's estimated deal value in rupees (null when not estimated).
            "dealValueEst": lead.dealValueEst,
        })
    return {"leads": out}


def autogrowth_analytics(user, business_id=None):
    """S9 — real counts for the Autogrowth > Analytics processing funnel.
    Stages are derived from LeadQuery's own stored fields (phone/status/tier) —
    no re-run of the creation-time scorer, no new columns. 'Agent verified' has
    no real backend signal yet (no agent-call-confirmation flow exists), so it
    is never counted here; the frontend renders it as the prototype's own
    locked/upsell stage for every seller until that signal exists for real."""
    from app_ib.models import Business, LeadQuery

    if business_id:
        biz = Business.objects.filter(id=business_id).first()
        if not biz:
            raise NotFound_("business not found")
        if biz.user_id != user.id:
            raise PermissionError_("not your business")
    else:
        biz = Business.objects.filter(user=user).first()
        if not biz:
            raise NotFound_("no business found for user")

    leads = list(LeadQuery.objects.filter(business=biz).values("phone", "status", "tier"))
    total = len(leads)
    contact_verified = sum(1 for l in leads if len("".join(c for c in (l["phone"] or "") if c.isdigit())) >= 10)
    genuine = sum(1 for l in leads if (l["status"] or "") != "quarantine")
    qualified = [l for l in leads if (l["tier"] or "") in ("A", "B")]
    tag_counts = {"Urgent": 0, "Intent": 0, "Interested": 0}
    for l in leads:
        tier = l["tier"] or ""
        if tier == "A":
            tag_counts["Urgent"] += 1
        elif tier == "B":
            tag_counts["Intent"] += 1
        elif tier in ("C", "D", "E"):
            tag_counts["Interested"] += 1

    return {
        "totalQueries": total,
        "stages": [
            {"name": "Contact verified", "n": contact_verified, "note": "real, reachable contact"},
            {"name": "Genuine", "n": genuine, "note": "spam & tyre-kickers removed"},
            {"name": "Intent & urgency", "n": len(qualified), "note": "timeline captured & scored"},
        ],
        "tagCounts": tag_counts,
    }


def create_manual_lead(user, data):
    """Seller-logged off-platform enquiry (dashboard '+ Enquiry': GMB call,
    WhatsApp, walk-in, referral…). Attaches to the caller's business so it shows
    up in their inbox/pipeline like any buyer-created lead."""
    from app_ib.models import Business, LeadQuery
    biz = Business.objects.filter(user=user).first()
    if not biz:
        raise NotFound_("no business found for user")
    extra = [f"{label}: {data.get(key)}" for key, label in
             (("quantity", "Quantity / scope"), ("estValue", "Estimated deal value"))
             if (data.get(key) or "").strip()]
    lead = LeadQuery.objects.create(
        business=biz, user=user,
        name=(data.get("buyerName") or "").strip(),
        phone=(data.get("phone") or "").strip(),
        city=(data.get("city") or "").strip(),
        interested=(data.get("lookingFor") or "").strip(),
        query="\n".join(extra),
        sourceChannel=(data.get("source") or "manual").strip(),
        formType="manual",
    )
    return {"leadId": lead.id}


# Valid kanban stages (mirror the frontend DealStage set — task 62).
_PIPELINE_STAGES = {"new", "contacted", "quoted", "meeting", "won", "lost"}


def set_lead_stage(user, lead_id, stage, deal_value=None):
    """Persist a lead's pipeline stage from a kanban drag (task 62). Owner-gated.
    F8: when the seller closes a deal (won/lost) the panel sends `deal_value` — the
    estimated/final deal value in rupees. Parse the digits out of whatever they typed
    ("₹6,00,000", "600000") and store it on dealValueEst (read by tasks 140/141)."""
    from app_ib.models import LeadQuery
    stage = (stage or "").strip().lower()
    if stage not in _PIPELINE_STAGES:
        raise Conflict_("invalid stage")
    lead = LeadQuery.objects.filter(id=lead_id).first()
    if not lead:
        raise NotFound_("lead not found")
    if not lead.business or lead.business.user_id != user.id:
        raise PermissionError_("not the business owner")
    lead.stage = stage
    update_fields = ["stage"]
    if deal_value is not None:
        digits = "".join(ch for ch in str(deal_value) if ch.isdigit())
        lead.dealValueEst = int(digits) if digits else None
        update_fields.append("dealValueEst")
    lead.save(update_fields=update_fields)
    return {"leadId": lead.id, "stage": stage, "dealValueEst": lead.dealValueEst}


def accept_lead(user, lead_id):
    from app_ib.models import LeadQuery, Conversation
    lead = LeadQuery.objects.filter(id=lead_id).first()
    if not lead:
        raise NotFound_("lead not found")
    if not lead.business or lead.business.user_id != user.id:
        raise PermissionError_("not the business owner")

    lead.leadStatus = "accepted"
    if lead.respondedAt is None:
        lead.respondedAt = timezone.now()
    if not isinstance(lead.logs, list):
        lead.logs = []
    lead.logs.append({
        "event": "lead accepted",
        "timestamp": timezone.now().strftime("%d %b %Y, %I:%M %p"),
    })
    lead.save(update_fields=["leadStatus", "respondedAt", "logs", "updatedAt"])

    # activate linked conversation if in requested state
    conv = Conversation.objects.filter(lead=lead, status=CONVERSATION_STATUS.REQUESTED).first()
    if conv:
        conv.status = CONVERSATION_STATUS.ACCEPTED
        conv.save(update_fields=["status", "updatedAt"])
    elif lead.user_id and not Conversation.objects.filter(lead=lead).exists():
        # lead→conversation bridge: accepting an enquiry from a signed-in buyer
        # opens the chat thread directly (no separate chat-request step)
        Conversation.objects.create(
            lead=lead, business=lead.business, clientUser=lead.user,
            businessUser=user, status=CONVERSATION_STATUS.ACCEPTED)

    return {"leadId": lead.id, "leadStatus": lead.leadStatus}


def decline_lead(user, lead_id, reason=""):
    from app_ib.models import LeadQuery, Conversation
    lead = LeadQuery.objects.filter(id=lead_id).first()
    if not lead:
        raise NotFound_("lead not found")
    if not lead.business or lead.business.user_id != user.id:
        raise PermissionError_("not the business owner")

    lead.leadStatus = "declined"
    lead.remark = reason or ""
    if not isinstance(lead.logs, list):
        lead.logs = []
    lead.logs.append({
        "event": f"lead declined: {reason}",
        "timestamp": timezone.now().strftime("%d %b %Y, %I:%M %p"),
    })
    lead.save(update_fields=["leadStatus", "remark", "logs", "updatedAt"])

    conv = Conversation.objects.filter(lead=lead, status=CONVERSATION_STATUS.REQUESTED).first()
    if conv:
        conv.status = CONVERSATION_STATUS.DECLINED
        conv.declineReason = reason[:255]
        conv.save(update_fields=["status", "declineReason", "updatedAt"])

    return {"leadId": lead.id, "leadStatus": lead.leadStatus}


def create_lead(user, data):
    """Buyer-facing enquiry/lead create — backend half of the universal connect
    wizard. Business-less leads are allowed (general project enquiries,
    architect-direct enquiries where the architect has no linked business, etc).
    Missing/invalid itemId never 500s — it just leaves business unresolved;
    only an explicit businessId that doesn't exist raises NotFound_."""
    from app_ib.models import Business, LeadQuery
    from interior_products.models import Product, Service, Catelogue
    from app_ib.engine_models import Shop, Architect
    from app_ib.Controllers.Engine.ChatController import CHAT_CONTROLLER

    item_type = (data.get("itemType") or "").strip().lower()
    item_id = data.get("itemId")
    intent = data.get("intent") or ""

    business = None
    product = service = catalouge = None
    if item_type and item_id:
        if item_type == "product":
            product = Product.objects.filter(id=item_id).first()
            business = product.business if product else None
        elif item_type == "service":
            service = Service.objects.filter(id=item_id).first()
            business = service.business if service else None
        elif item_type == "catalogue":
            catalouge = Catelogue.objects.filter(id=item_id).first()
            business = catalouge.business if catalouge else None
        elif item_type == "shop":
            shop = Shop.objects.filter(id=item_id).first()
            business = shop.business if shop else None
        elif item_type == "architect":
            architect = Architect.objects.filter(id=item_id).first()
            business = architect.businesses.first() if architect else None
        # unresolved id / unknown itemType -> business stays None, no 500
    elif data.get("businessId"):
        business = Business.objects.filter(id=data["businessId"]).first()
        if not business:
            raise NotFound_("business not found")

    # Self-enquiry guard: a seller can't enquire on their own listing.
    if business and business.user_id and business.user_id == user.id:
        raise Conflict_("You can't send an enquiry to your own listing")

    profile = getattr(user, "user_profile", None)
    name = data.get("name") or (profile.name if profile else "") or ""
    phone = data.get("phone") or (profile.phone if profile else "") or ""
    email = (profile.email if profile else "") or ""

    enquiry_type = data.get("enquiryType") or ""
    item_name = data.get("itemName") or ""
    interested = f"{intent.capitalize() or 'General'} enquiry"
    if enquiry_type:
        interested += f" — {enquiry_type}"
    if item_name:
        interested += f" — {item_name}"

    fields = data.get("fields") or {}
    query_text = "\n".join(f"{k}: {v}" for k, v in fields.items() if v not in (None, "", []))

    # Map the connect-wizard's timeline tokens → canonical LeadQuery.timeline
    # choices (task 33). The wizard uses UI-facing tokens that differ per intent
    # (project/catalogue: now/soon/later; service: week/month/ahead/unsure).
    # Canonical values pass through unchanged (classic/admin paths already send them).
    _WIZARD_TIMELINE = {
        "now": "30d", "soon": "90d", "later": "90plus", "browsing": "browsing",
        "week": "30d", "month": "90d", "ahead": "90plus", "unsure": "browsing",
        "30d": "30d", "90d": "90d", "90plus": "90plus",
    }
    timeline = _WIZARD_TIMELINE.get((fields.get("timeline") or "").strip(), "")

    # backfill city/state/country from the buyer's saved location, same source
    # QueryTasks.CreateLeadQueryTask reads for the classic (non-engine) query form
    city = state = country = ""
    loc = getattr(user, "user_location", None)
    if loc:
        city = loc.city or ""
        state = loc.locationState.name if loc.locationState_id else ""
        country = loc.locationCountry.name if loc.locationCountry_id else ""

    lead = LeadQuery.objects.create(
        user=user, name=name, phone=phone, email=email, business=business,
        interested=interested, query=query_text, city=city, state=state, country=country,
        category=item_type or intent, timeline=timeline,
        sourceChannel="connect_wizard", formType=intent, originType=item_type or "",
        originId=item_id or None,
        product=product, service=service, catalouge=catalouge,
    )

    # Qualification score+tier from the weights singleton (task 33). Creation-only,
    # like the classic path; never let a scoring hiccup fail the enquiry.
    try:
        from app_ib.Controllers.Query.Tasks.QueryTasks import compute_score_and_tier
        from interior_admin.models import QualificationWeightConfig
        from interior_admin.Controllers.Weights.WeightsController import merged_weights
        cfg, _ = QualificationWeightConfig.objects.get_or_create(id=1)
        lead.score, lead.tier = compute_score_and_tier(lead, merged_weights(cfg.weights))
        lead.save(update_fields=["score", "tier"])
    except Exception:
        logger.exception("create_lead: scoring failed for lead %s", lead.id)

    # bridge into chat only when there's a business with a real owner who isn't
    # the buyer themself — never let a chat failure fail the lead
    conv_id = None
    if business and business.user_id and business.user_id != user.id:
        try:
            conv = CHAT_CONTROLLER.start_conversation(user, business.id, lead.id)
            conv_id = conv.get("conversationId")
        except Exception:
            logger.exception("create_lead: chat bridge failed for lead %s", lead.id)

    return {"leadId": lead.id, "conversationId": conv_id}


# ---------------------------------------------------------------------------
# 11. Platform ads
# ---------------------------------------------------------------------------
def _ad_creative(asset):
    """Pull the render creative out of an AdAsset. Creative is a free-form JSON
    blob (AdAsset.meta) + the image URL (AdAsset.s3Key), so tolerate key variants
    from the business ad-builder and the admin fallback authoring alike."""
    if asset is None:
        return {}
    m = asset.meta or {}

    def pick(*keys):
        for k in keys:
            v = m.get(k)
            if v:
                return v
        return ""

    return {
        "eyebrow": pick("eyebrow"),
        "heading1": pick("heading1", "headline", "title", "heading"),
        "heading2": pick("heading2", "subheading"),
        "description": pick("description", "sub", "subtitle", "body"),
        "features": m.get("features") or [],
        "buttonLabel": pick("buttonLabel", "ctaLabel", "cta"),
        # no "link" fallback: in legacy prod assets meta['link'] is the IMAGE url,
        # not a CTA destination (migrate_prod_repair remaps it to imageUrl)
        "buttonLink": pick("buttonLink", "ctaUrl", "ctaLink"),
        "imageUrl": pick("imageUrl", "image") or asset.s3Key,
        "theme": pick("theme") or "green",
    }


def get_ads(page_slug="", placement=""):
    # Unified ad render path (task 16): render live AdCampaigns (the model admin
    # moderates), NOT the retired PlatformAd. A slot shows PAID ads (advertiser
    # set) when any match; otherwise it falls back to house ads (advertiser null).
    from interior_advertisement.models import AdCampaign
    now = timezone.now()
    qs = (
        AdCampaign.objects.filter(status__code="active")  # NAMES.ACTIVE = live
        .filter(startDate__lte=now, endDate__gte=now)
        .select_related("advertiser", "placement")
        .prefetch_related("assets")
    )
    if placement:
        qs = qs.filter(placement__code=placement)
    if page_slug:
        # House ads target a page; paid ads (page="") match any page.
        qs = qs.filter(Q(page=page_slug) | Q(page=""))
    qs = qs.order_by("-priceTotal", "-createdAt")

    live = list(qs)
    paid = [c for c in live if c.advertiser_id]
    chosen = paid if paid else [c for c in live if not c.advertiser_id]

    ads = []
    for c in chosen:
        assets = list(c.assets.all())
        cr = _ad_creative(assets[0] if assets else None)
        ads.append({
            "id": c.id,
            "page": c.page or "",
            "placement": c.placement.code if c.placement_id else "",
            "eyebrow": cr.get("eyebrow", ""),
            "heading1": cr.get("heading1") or (c.title or ""),
            "heading2": cr.get("heading2", ""),
            "description": cr.get("description", ""),
            "features": cr.get("features", []),
            "buttonLabel": cr.get("buttonLabel", ""),
            "buttonLink": cr.get("buttonLink", ""),
            "imageUrl": cr.get("imageUrl", ""),
            "theme": cr.get("theme", "green"),
            "displayOrder": 0,
            # "Sponsored by X" line; empty for house/fallback ads.
            "sponsoredBy": (getattr(c.advertiser, "businessName", "") or "") if c.advertiser_id else "",
        })
    # ponytail: impression tracking dropped with PlatformAd; AdCampaign has no
    # counter yet. Re-add via AdEvent when analytics needs it.
    return {"page": page_slug, "ads": ads}


def click_ad(ad_id):
    # ponytail: click tracking not yet modelled on AdCampaign (PlatformAd counters
    # retired). Accept the ping so the best-effort frontend call succeeds; wire to
    # AdEvent when ad analytics is built.
    return {"ok": True}


# ---------------------------------------------------------------------------
# 13. shops/mine/ — authenticated list of shops owned by the request user
# ---------------------------------------------------------------------------
def my_shops(user):
    """Return all Shop rows owned by user (including inactive), newest first."""
    from app_ib.models import Shop
    qs = Shop.objects.select_related("business").filter(user=user).order_by("-timestamp")
    items = []
    for s in qs:
        d = _shop_full_dict(s, include_videos=False, include_details=False)
        # add owner-only fields (already on the model; _shop_full_dict omits isActive)
        d["isActive"] = s.isActive
        d["completionPercent"] = s.completionPercent
        d["canGoLive"] = s.canGoLive
        d["leadCount"] = s.leadCount
        d["viewCount"] = s.viewCount
        items.append(d)
    return {"items": items, "total": len(items)}


# ---------------------------------------------------------------------------
# 14. architects/mine/ — authenticated list of architects owned by the request user
# ---------------------------------------------------------------------------
def my_architects(user):
    """Return all Architect rows owned by user (including inactive), newest first."""
    from app_ib.models import Architect, Project
    from django.db.models import Count as _Count
    qs = (Architect.objects.filter(user=user)
          .annotate(_project_count=_Count("projects"))
          .order_by("-timestamp"))
    items = []
    for a in qs:
        d = _arch_full_dict(a, include_details=False,
                            project_count=getattr(a, "_project_count", 0))
        # add owner-only fields
        d["isActive"] = a.isActive
        d["completionPercent"] = a.completionPercent
        d["canGoLive"] = a.canGoLive
        d["leadCount"] = a.leadCount
        d["viewCount"] = a.viewCount
        d["projectCount"] = getattr(a, "_project_count", 0)
        items.append(d)
    return {"items": items, "total": len(items)}


# ---------------------------------------------------------------------------
# 14b. my/plans/ — authenticated buying history: union of the user's
#      BusinessPlan + ShopPlan + ArchitectPlan (buy-first model, Prompt 6).
# ---------------------------------------------------------------------------
def _plan_row(p, entity_type, entity):
    return {
        "id": p.id,
        "entityType": entity_type,
        "entityId": entity.id if entity else None,
        "planId": p.plan_id,
        "planName": p.plan.title if p.plan_id else None,
        "tier": p.plan.tier if p.plan_id else None,
        "amount": p.amount,
        "isActive": p.isActive,
        "status": p.status,
        "transactionId": p.transactionId,
        "expireDate": p.expireDate.strftime("%Y-%m-%d") if p.expireDate else None,
        "lastActivate": p.lastActivate.strftime("%Y-%m-%d") if p.lastActivate else None,
        "timestamp": p.timestamp.strftime("%Y-%m-%d") if p.timestamp else None,
    }


def my_plans(user):
    """Buying history + entitlement signals — delegated to the EntitlementService, the
    single source of truth for the plan registry + grantsEntityTypes bundle expansion.
    Returns items (incl. automation), activeEntityTypes (active → publishing gate) and
    entitledEntityTypes (active-or-pending → tab visibility)."""
    from app_ib.Controllers.Plans.EntitlementService import ENTITLEMENT_SERVICE
    return ENTITLEMENT_SERVICE.my_plans(user)


# ---------------------------------------------------------------------------
# my/invoices/ — billing history for the logged-in user.
# Joins TransectionData with the user's entity plans to enrich each payment
# row with the plan name and entity type.
# ---------------------------------------------------------------------------
def my_invoices(user):
    from app_ib.models import BusinessPlan, ShopPlan, ArchitectPlan, TransectionData
    from django.db.models import Q

    # Collect all transaction ids owned by this user across every plan type.
    txn_plan_map = {}  # transactionId -> (planName, entityType)
    for p in BusinessPlan.objects.filter(Q(user=user) | Q(business__user=user)).select_related("plan"):
        if p.transactionId:
            txn_plan_map[p.transactionId] = (
                p.plan.title if p.plan_id else "",
                ENTITY_TYPE.BUSINESS,
            )
    for p in ShopPlan.objects.filter(user=user).select_related("plan"):
        if p.transactionId:
            txn_plan_map[p.transactionId] = (
                p.plan.title if p.plan_id else "",
                ENTITY_TYPE.SHOP,
            )
    for p in ArchitectPlan.objects.filter(user=user).select_related("plan"):
        if p.transactionId:
            txn_plan_map[p.transactionId] = (
                p.plan.title if p.plan_id else "",
                ENTITY_TYPE.ARCHITECT,
            )

    if not txn_plan_map:
        return {"items": [], "total": 0}

    txns = TransectionData.objects.filter(
        transactionId__in=list(txn_plan_map.keys())
    ).order_by("-createdAt")

    items = []
    for t in txns:
        plan_name, entity_type = txn_plan_map.get(t.transactionId, ("", ""))
        items.append({
            "id": t.id,
            "transactionId": t.transactionId,
            "orderId": t.orderId,
            "amount": t.amount,
            "status": t.orderStatus,
            "paymentFor": t.paymentFor,
            "planName": plan_name,
            "entityType": entity_type,
            "date": t.createdAt.strftime("%Y-%m-%d") if t.createdAt else None,
        })
    return {"items": items, "total": len(items)}


# ---------------------------------------------------------------------------
# my/activity/ — recent view/click event feed for the logged-in user.
# Merges ViewEvent and ClickEvent rows, resolves the generic FK to a display
# name, and returns a unified activity list newest-first.
# ---------------------------------------------------------------------------
def my_activity(user, limit=30):
    from app_ib.engine_models import ViewEvent, ClickEvent
    from django.contrib.contenttypes.models import ContentType

    view_rows = list(
        ViewEvent.objects.filter(user=user)
        .select_related("contentType")
        .order_by("-timestamp")[:limit]
    )
    click_rows = list(
        ClickEvent.objects.filter(user=user)
        .select_related("contentType")
        .order_by("-timestamp")[:limit]
    )

    # Build a combined list with a unified shape, then sort.
    combined = []
    for v in view_rows:
        combined.append({
            "_kind": "view",
            "_clickType": "",
            "_ct": v.contentType,
            "_oid": v.objectId,
            "_ts": v.timestamp,
            "_id": v.id,
        })
    for c in click_rows:
        combined.append({
            "_kind": "click",
            "_clickType": c.clickType or "",
            "_ct": c.contentType,
            "_oid": c.objectId,
            "_ts": c.timestamp,
            "_id": c.id,
        })
    combined.sort(key=lambda x: x["_ts"], reverse=True)
    combined = combined[:limit]

    # Hydrate entity names (batch fetch per content type to avoid N+1).
    ct_groups = {}
    for row in combined:
        ct = row["_ct"]
        if ct:
            ct_groups.setdefault(ct.id, (ct, set()))[1].add(row["_oid"])

    entity_cache = {}  # (ct_id, object_id) -> (entity_type_str, name, slug)
    for ct_id, (ct, oids) in ct_groups.items():
        model_class = ct.model_class()
        if model_class is None:
            continue
        objs = {o.id: o for o in model_class.objects.filter(id__in=oids)}
        for oid, obj in objs.items():
            from app_ib.Controllers.Engine.EngineController import _name
            entity_cache[(ct_id, oid)] = (
                ct.model,
                _name(obj),
                getattr(obj, "slug", "") or "",
            )

    items = []
    for row in combined:
        ct = row["_ct"]
        oid = row["_oid"]
        key = (ct.id, oid) if ct else None
        entity_type, entity_name, slug = entity_cache.get(key, ("", "", "")) if key else ("", "", "")
        kind = row["_kind"]
        click_type = row["_clickType"]
        action = "Viewed" if kind == "view" else (f"Clicked {click_type}" if click_type else "Clicked")
        items.append({
            "id": row["_id"],
            "kind": kind,
            "action": action,
            "entityType": entity_type,
            "entityName": entity_name,
            "slug": slug,
            "timestamp": row["_ts"].isoformat(),
        })
    return {"items": items, "total": len(items)}


# ---------------------------------------------------------------------------
# my/engagement/ — inbound "recent activity" feed for the logged-in seller:
#   what OTHER users did to the seller's OWN entities (business / shop / architect
#   profile / product / service) — "someone viewed your product", "someone saved
#   your shop", "someone filled your form". Reads the denormalized
#   EngagementActivity store keyed by `owner`, so it's a single indexed query.
#   (Distinct from my_activity, which is the seller's OWN browsing history.)
# ---------------------------------------------------------------------------
def engagement_feed(user, limit=30):
    from app_ib.engine_models import EngagementActivity
    from app_ib.Utils.EngineConfig import ENGAGEMENT_VERB

    rows = list(
        EngagementActivity.objects.filter(owner=user).order_by("-timestamp")[:limit]
    )
    items = []
    for r in rows:
        actor = r.actorName or ENGAGEMENT_VERB.ANON_ACTOR
        phrase = ENGAGEMENT_VERB.LABELS.get(r.verb, r.verb)
        kind = r.entityType or "listing"
        # Human one-liner, e.g. "Someone viewed your product" /
        # "Riya filled a form on your business".
        action = f"{actor} {phrase} your {kind}".strip()
        items.append({
            "id": r.id,
            "verb": r.verb,
            "action": action,
            "actorName": actor,
            "entityType": r.entityType or "",
            "entityName": r.entityName or "",
            "count": r.count or 1,
            "isRead": bool(r.isRead),
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
        })
    unread = EngagementActivity.objects.filter(owner=user, isRead=False).count()
    return {"items": items, "total": len(items), "unreadCount": unread}


def engagement_mark_read(user):
    """Mark all of the seller's inbound-engagement rows as read. Returns the count
    of rows flipped."""
    from app_ib.engine_models import EngagementActivity
    return EngagementActivity.objects.filter(owner=user, isRead=False).update(isRead=True)


# ---------------------------------------------------------------------------
# my/quotations/ — leads received by the logged-in seller's business.
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Quotations (task 63) — real seller-built quotation documents (create/update/
# status) that replace the old lead-derived placeholder. Line items + buyer/seller
# blocks are JSON snapshots; money totals are RECOMPUTED server-side on every write.
# ---------------------------------------------------------------------------
_QUOTATION_STATUSES = {"sent", "viewed", "accepted", "declined"}


def _sanitize_line_items(raw):
    items = []
    for li in (raw or []):
        if not isinstance(li, dict):
            continue
        try:
            qty = float(li.get("qty") or 0)
        except (TypeError, ValueError):
            qty = 0.0
        try:
            rate = float(li.get("rate") or 0)
        except (TypeError, ValueError):
            rate = 0.0
        items.append({
            "id": str(li.get("id") or ""),
            "type": "service" if (li.get("type") == "service") else "product",
            "description": (li.get("description") or "").strip(),
            "code": (li.get("code") or ""),
            "qty": qty,
            "unit": (li.get("unit") or ""),
            "rate": rate,
            "amount": round(qty * rate, 2),
        })
    return items


def _compute_totals(items, gst_percent):
    from decimal import Decimal, ROUND_HALF_UP
    cents = Decimal("0.01")
    subtotal = sum((Decimal(str(li["amount"])) for li in items), Decimal("0"))
    try:
        gst = Decimal(str(gst_percent or 0))
    except Exception:
        gst = Decimal("0")
    subtotal = subtotal.quantize(cents, rounding=ROUND_HALF_UP)
    gst_amount = (subtotal * gst / Decimal("100")).quantize(cents, rounding=ROUND_HALF_UP)
    grand = (subtotal + gst_amount).quantize(cents, rounding=ROUND_HALF_UP)
    return subtotal, gst_amount, grand


def _parse_quote_date(s):
    if not s:
        return None
    from django.utils.dateparse import parse_date
    return parse_date(str(s)[:10])


def _quotation_dict(q):
    return {
        "id": str(q.id),
        "number": q.number,
        "enquiryId": (f"IB-{q.lead_id}" if q.lead_id else None),
        "status": q.status,
        "pricingMode": q.pricingMode,
        "createdAt": q.createdAt.isoformat() if q.createdAt else "",
        "sentAt": (q.sentAt or q.createdAt).isoformat() if (q.sentAt or q.createdAt) else "",
        "validUntil": q.validUntil.isoformat() if q.validUntil else "",
        "from": q.fromBlock or {},
        "to": q.toBlock or {},
        "lineItems": q.lineItems or [],
        "subtotal": float(q.subtotal or 0),
        "gstPercent": float(q.gstPercent or 0),
        "gstAmount": float(q.gstAmount or 0),
        "grandTotal": float(q.grandTotal or 0),
        "terms": q.terms or "",
        "noteToBuyer": q.noteToBuyer or "",
    }


def team_members():
    """About-page team members from the backend (task 77)."""
    from app_ib.engine_models import TeamMember
    return [{"name": m.name, "role": m.role, "initials": m.initials,
             "gradient": m.gradient, "photoUrl": m.photoUrl, "bio": m.bio,
             "placeholder": m.isPlaceholder}
            for m in TeamMember.objects.filter(isActive=True)]


def help_content():
    """Help-centre content from the backend (task 76): FAQs, topic tiles and video
    tutorials. Section headings/labels stay static in the frontend."""
    from app_ib.engine_models import HelpFaq, HelpTopic, HelpTutorial
    faqs = [{"q": f.question, "a": f.answer}
            for f in HelpFaq.objects.filter(isActive=True)]
    topics = [{"title": t.title, "icon": t.icon, "iconBg": t.iconBg,
               "iconColor": t.iconColor, "count": f"{t.articleCount} articles"}
              for t in HelpTopic.objects.filter(isActive=True)]
    tutorials = [{"title": t.title, "gradient": t.gradient, "duration": t.duration,
                  "views": t.views, "videoUrl": t.videoUrl}
                 for t in HelpTutorial.objects.filter(isActive=True)]
    return {"faqs": faqs, "topics": topics, "tutorials": tutorials}


def _ticket_dict(t):
    return {
        "id": t.id, "subject": t.subject, "message": t.message, "status": t.status,
        "createdAt": t.createdAt.isoformat() if t.createdAt else "",
        "lastReplyAt": t.lastReplyAt.isoformat() if t.lastReplyAt else "",
    }


def create_ticket(user, data):
    """Raise a support ticket (task 76). Auth optional — anonymous needs an email."""
    from app_ib.engine_models import SupportTicket
    data = data or {}
    subject = (data.get("subject") or "").strip()
    message = (data.get("message") or "").strip()
    if not subject or not message:
        raise Conflict_("subject and message are required")
    auth_user = user if getattr(user, "is_authenticated", False) else None
    email = (data.get("email") or "").strip()
    if not auth_user and not email:
        raise Conflict_("an email is required to raise a ticket")
    t = SupportTicket.objects.create(
        user=auth_user, email=email, subject=subject[:200], message=message, status="open")
    return _ticket_dict(t)


def my_tickets(user):
    """The logged-in user's support tickets, newest first (task 76)."""
    from app_ib.engine_models import SupportTicket
    if not getattr(user, "is_authenticated", False):
        return {"items": [], "openCount": 0}
    rows = list(SupportTicket.objects.filter(user=user)[:50])
    return {"items": [_ticket_dict(t) for t in rows],
            "openCount": sum(1 for t in rows if t.status in ("open", "in_progress"))}


def support_config():
    """Single source of truth for support/contact channels (task 75). Serves the
    singleton SupportConfig row; falls back to the real email only when unseeded."""
    from app_ib.engine_models import SupportConfig
    cfg = SupportConfig.objects.first()
    if not cfg:
        return {"email": "help@interiorbazzar.com", "phone": "", "whatsapp": "",
                "tollFree": "", "officeAddress": "", "hours": "",
                "liveChatAvailable": False, "agentCount": 0}
    return {
        "email": cfg.supportEmail, "phone": cfg.phone, "whatsapp": cfg.whatsapp,
        "tollFree": cfg.tollFree, "officeAddress": cfg.officeAddress, "hours": cfg.hours,
        "liveChatAvailable": cfg.liveChatAvailable, "agentCount": cfg.agentCount,
    }


def brand_logo():
    """Public: today's active brand logo + tagline (task 27). The resolver lives
    in interior_admin; lazy-imported here to avoid a core→admin import cycle."""
    from interior_admin.Controllers.BrandAsset.BrandAssetController import resolve_active_logo
    return resolve_active_logo()


def my_quotations(user, limit=50):
    """List the seller's own saved quotation documents, newest first."""
    from app_ib.engine_models import Quotation
    rows = list(Quotation.objects.filter(user=user).order_by("-createdAt")[:limit])
    return {"items": [_quotation_dict(q) for q in rows], "total": len(rows)}


def _valid_lines_or_raise(raw):
    items = _sanitize_line_items(raw)
    valid = [li for li in items if li["description"] and li["qty"] > 0 and li["rate"] > 0]
    if not valid:
        raise Conflict_("at least one line item with a description, quantity and rate is required")
    return valid


def create_quotation(user, data):
    from app_ib.engine_models import Quotation
    from app_ib.models import Business, LeadQuery
    data = data or {}
    to_block = data.get("to") or {}
    if not (to_block.get("name") or "").strip():
        raise Conflict_("buyer name is required")
    valid_items = _valid_lines_or_raise(data.get("lineItems"))
    gst_percent = data.get("gstPercent") or 0
    subtotal, gst_amount, grand = _compute_totals(valid_items, gst_percent)
    status = (data.get("status") or "sent").strip().lower()
    if status not in _QUOTATION_STATUSES:
        status = "sent"
    biz = Business.objects.filter(user=user).first()
    lead = None
    lead_id = data.get("leadId")
    if lead_id:
        lead = LeadQuery.objects.filter(id=lead_id, business=biz).first()
    number = (data.get("number") or "").strip() or f"IB-Q-{int(timezone.now().timestamp())}"
    q = Quotation.objects.create(
        user=user, business=biz, lead=lead,
        number=number, status=status,
        pricingMode=(data.get("pricingMode") or "custom"),
        validUntil=_parse_quote_date(data.get("validUntil")),
        fromBlock=(data.get("from") or {}), toBlock=to_block,
        lineItems=valid_items,
        subtotal=subtotal, gstPercent=gst_percent, gstAmount=gst_amount, grandTotal=grand,
        terms=(data.get("terms") or ""), noteToBuyer=(data.get("noteToBuyer") or ""),
        sentAt=timezone.now(),
    )
    return _quotation_dict(q)


def update_quotation(user, quotation_id, data):
    from app_ib.engine_models import Quotation
    q = Quotation.objects.filter(id=quotation_id).first()
    if not q:
        raise NotFound_("quotation not found")
    if q.user_id != user.id:
        raise PermissionError_("not the quotation owner")
    data = data or {}
    if "to" in data:
        to_block = data.get("to") or {}
        if not (to_block.get("name") or "").strip():
            raise Conflict_("buyer name is required")
        q.toBlock = to_block
    if "from" in data:
        q.fromBlock = data.get("from") or {}
    if "lineItems" in data:
        q.lineItems = _valid_lines_or_raise(data.get("lineItems"))
    if "gstPercent" in data:
        q.gstPercent = data.get("gstPercent") or 0
    # Always recompute totals from the (possibly updated) items + gstPercent.
    q.subtotal, q.gstAmount, q.grandTotal = _compute_totals(q.lineItems, q.gstPercent)
    if "validUntil" in data:
        q.validUntil = _parse_quote_date(data.get("validUntil"))
    if "terms" in data:
        q.terms = data.get("terms") or ""
    if "noteToBuyer" in data:
        q.noteToBuyer = data.get("noteToBuyer") or ""
    if "pricingMode" in data:
        q.pricingMode = data.get("pricingMode") or "custom"
    if (data.get("number") or "").strip():
        q.number = data["number"].strip()
    if data.get("status"):
        st = str(data["status"]).strip().lower()
        if st in _QUOTATION_STATUSES:
            q.status = st
    q.save()
    return _quotation_dict(q)


def set_quotation_status(user, quotation_id, status):
    from app_ib.engine_models import Quotation
    st = (status or "").strip().lower()
    if st not in _QUOTATION_STATUSES:
        raise Conflict_("invalid status")
    q = Quotation.objects.filter(id=quotation_id).first()
    if not q:
        raise NotFound_("quotation not found")
    if q.user_id != user.id:
        raise PermissionError_("not the quotation owner")
    q.status = st
    q.save(update_fields=["status", "updatedAt"])
    return _quotation_dict(q)


def _quotation_message_body(q):
    """Human-readable quote summary posted into the buyer's chat thread (F12)."""
    total = f"₹{float(q.grandTotal or 0):,.0f}"
    lines = [f"📄 Quotation {q.number} — {total}"]
    if q.validUntil:
        lines.append(f"Valid until {q.validUntil.strftime('%d %b %Y')}")
    note = (q.noteToBuyer or "").strip()
    if note:
        lines.append(note)
    return "\n".join(lines)


def send_quotation(user, quotation_id):
    """F12: mark a quotation sent AND actually deliver it to the buyer. When the
    quotation's lead has a platform buyer, post a quote-summary chat message into the
    lead's conversation (creating/reopening it as needed) via the chat controller —
    which pushes to the buyer's SSE stream and raises an unread notification, so the
    buyer genuinely receives it. Off-platform leads (no buyer user) get sent-state
    only (delivered=False); the send itself still succeeds. Owner-gated."""
    from app_ib.engine_models import Quotation
    from app_ib.models import Conversation
    from app_ib.Controllers.Engine.ChatController import CHAT_CONTROLLER
    q = Quotation.objects.filter(id=quotation_id).first()
    if not q:
        raise NotFound_("quotation not found")
    if q.user_id != user.id:
        raise PermissionError_("not the quotation owner")
    q.status = "sent"
    q.sentAt = timezone.now()
    q.save(update_fields=["status", "sentAt", "updatedAt"])

    delivered = False
    buyer = q.lead.user if (q.lead_id and q.lead) else None
    if buyer:
        conv = Conversation.objects.filter(lead=q.lead).first()
        if not conv:
            conv = Conversation.objects.create(
                lead=q.lead, business=q.business, clientUser=buyer,
                businessUser=user, status=CONVERSATION_STATUS.ACCEPTED)
        elif conv.status not in (CONVERSATION_STATUS.ACCEPTED, CONVERSATION_STATUS.REQUESTED):
            # a declined/closed thread is reopened so the quote can land
            conv.status = CONVERSATION_STATUS.ACCEPTED
            conv.save(update_fields=["status", "updatedAt"])
        CHAT_CONTROLLER.send_message(user, conv.id, _quotation_message_body(q))
        delivered = True

    data = _quotation_dict(q)
    data["delivered"] = delivered
    return data


# ---------------------------------------------------------------------------
# plans/templates/ — public Subscription catalogue, optionally by entityType.
#   Each row carries `key` (= Subscription.tag = the v3 plan key) so the v3
#   checkout can resolve a chosen plan card to a real Subscription id.
# ---------------------------------------------------------------------------
def server_time(user=None):
    """Backend-authoritative clock (flow.txt LINE 11). Returns the server 'now' + the
    user's login-time anchor so the client can compute a skew and never trust local Date
    for any decision (those are re-validated server-side at action time)."""
    from django.utils import timezone
    now = timezone.now()
    login_time = None
    if user is not None and getattr(user, "is_authenticated", False):
        lt = getattr(user, "last_login", None)
        login_time = lt.isoformat() if lt else None
    return {
        "serverNow": now.isoformat(),
        "epochMs": int(now.timestamp() * 1000),
        "loginTime": login_time,
    }


def payment_card(user, transaction_id):
    """Single buying-history card for one transaction (used by the manual re-check,
    Prompt 10). Returns the plan row + live payment `status`, scoped to the owner."""
    from app_ib.models import BusinessPlan, ShopPlan, ArchitectPlan, AutomationPlan, TransectionData
    txn = TransectionData.objects.filter(transactionId=transaction_id).first()
    status = txn.orderStatus if txn else None
    for Model, etype, fk in (
        (BusinessPlan, ENTITY_TYPE.BUSINESS, "business"),
        (ShopPlan, ENTITY_TYPE.SHOP, "shop"),
        (ArchitectPlan, ENTITY_TYPE.ARCHITECT, "architect"),
        (AutomationPlan, ENTITY_TYPE.AUTOMATION, None),
    ):
        related = ["plan"] + ([fk] if fk else [])
        p = Model.objects.select_related(*related).filter(transactionId=transaction_id).first()
        if not p:
            continue
        entity = getattr(p, fk, None) if fk else None
        owner_id = p.user_id or (getattr(entity, "user_id", None) if entity else None)
        if owner_id and owner_id != user.id:
            raise PermissionError_("not your payment")
        row = _plan_row(p, etype, entity)
        row["status"] = status
        row["unverified"] = not p.isActive
        return row
    return {"transactionId": transaction_id, "status": status, "found": False}


def create_manual_plan(user, plan_id, transaction_id, proof_url="", cycle_id=None):
    """Manual (offline) payment path: the buyer pays by bank/UPI transfer off-site,
    then submits their transaction/UTR id (and optionally a proof image) here. We
    create the chosen entity plan INACTIVE (entity FK null — buy-first) recording
    that id, record a SUBMITTED manual TransectionData so it surfaces in the admin
    payments queue, and flip the buyer to a SELLER immediately so they can open the
    seller dashboard. The plan stays pending until an admin verifies the transfer and
    activates it (admin Verify → ActivateEntityPlan), which is what unlocks entity
    creation. Gateway (Cashfree) is the other, instant-activation path."""
    from asgiref.sync import async_to_sync
    from django.db import transaction
    from django.utils import timezone
    from dateutil.relativedelta import relativedelta
    from app_ib.models import Subscription, TransectionData, PlanBillingCycle
    from app_ib.Controllers.Plans.PlanController import PLAN_CONTROLLER
    from app_ib.Utils.Names import NAMES

    txn = (transaction_id or "").strip()
    if not txn:
        raise ValueError("transactionId required")
    sub = Subscription.objects.filter(id=plan_id, isActive=True, is_delete=False).first()
    if not sub:
        raise NotFound_("plan not found")

    # Chosen billing cycle (explicit, else the plan's only/lowest active cycle) — its
    # price is what the buyer transferred and what surfaces in the admin payments queue.
    cyc = (PlanBillingCycle.objects.filter(plan_id=sub.id, id=cycle_id, isActive=True).first()
           if cycle_id else None)
    if not cyc:
        cyc = PlanBillingCycle.objects.filter(plan_id=sub.id, isActive=True).order_by("durationMonths").first()
    if cyc:
        cyc_amount = str(int(cyc.price)) if cyc.price == cyc.price.to_integral_value() else str(cyc.price)
    else:
        cyc_amount = str(sub.amount or "")

    # Idempotent on the transaction id: a buyer re-submitting the same UTR must NOT
    # create a second plan/txn. A duplicate plan would break admin-Verify, whose
    # ActivateEntityPlan does .get(transactionId=…) and raises on multiple rows.
    if not TransectionData.objects.filter(transactionId=txn).exists():
        with transaction.atomic():
            # Inactive entity plan for this user (routes by Subscription.entityType).
            resp = async_to_sync(PLAN_CONTROLLER.CreateEntityPlan)(
                planId=sub.id, userId=user.id, transectionId=txn, cycleId=cycle_id
            )
            if not resp or not getattr(resp, "response", False):
                raise ValueError(getattr(resp, "message", "could not create plan") if resp else "could not create plan")

            # Record the payment as a SUBMITTED manual transaction so it surfaces in
            # the admin Payments queue (task 11 Verify → ActivateEntityPlan finds the
            # plan by this same txn id). Committed atomically with the plan.
            now = timezone.now()
            TransectionData.objects.create(
                orderId=txn, transactionId=txn, amount=cyc_amount,
                paymentFor=NAMES.PLAN, paymentMethod="manual", orderStatus="SUBMITTED",
                proofUrl=(proof_url or "").strip(),
                createdAt=now, expiryAt=now + relativedelta(days=7),
            )

    # Become a seller now (dashboard access) — verification is still pending.
    if user.type != NAMES.BUSINESS:
        user.type = NAMES.BUSINESS
        user.save(update_fields=["type"])

    # Return the freshly-created (pending) card.
    return payment_card(user, txn)


def _fmt_inr(n):
    """₹ with Indian digit grouping (₹2,12,399)."""
    s = str(int(round(n)))
    if len(s) <= 3:
        return "₹" + s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return "₹" + ",".join(parts + [tail])


def _cycle_label(n):
    """durationMonths -> (cycle key, period label). ONE unit: months."""
    key = {1: "1m", 3: "3m", 6: "6m", 12: "1y"}.get(n, f"{n}m")
    period = {1: "/month", 12: "/year"}.get(n, f"/{n} months")
    return key, period


def _plan_cycles(s):
    """Billing cycles for the public plans page, straight from the PlanBillingCycle
    child rows (money source of truth). Only active cycles, cheapest→dearest. Prices
    formatted ₹ Indian grouping, GST-inclusive; oldPrice/badgeLabel from the row."""
    out = []
    for c in s.billingCycles.filter(isActive=True).order_by("durationMonths"):
        n = int(c.durationMonths or 0)
        key, period = _cycle_label(n)
        price = _fmt_inr(c.price)
        entry = {
            "id": c.id,
            "cycle": key,
            "durationMonths": n,
            "price": price,
            "period": period,
            "gstLine": "incl. GST",
            "total": price,
            "badgeLabel": c.badgeLabel or period.lstrip("/"),
        }
        if c.oldPrice and c.oldPrice > c.price:
            entry["oldPrice"] = _fmt_inr(c.oldPrice)
            entry["savingNote"] = f"Save {_fmt_inr(c.oldPrice - c.price)}"
        out.append(entry)
    return out


def plan_templates(entity_type=""):
    from app_ib.models import Subscription
    qs = list(Subscription.objects.filter(isActive=True, is_delete=False))
    if entity_type:
        qs = [s for s in qs if s.entityType == entity_type]
    qs.sort(key=lambda s: (s.tier or 0, s.id))
    # Full v3 display catalogue: ONE item per plan (multi-cycle plans are one
    # Subscription row + PlanBillingCycle children now). Per-cycle pricing comes
    # straight from the child rows — the frontend renders a per-card cycle selector.
    items = [{
        "id": s.id,
        "key": s.tag or "",
        "title": s.title,
        "amount": s.amount,
        "entityType": s.entityType,
        "tier": s.tier,
        "duration": s.duration,
        "family": s.planFamily,
        "badge": s.badge,
        "badgeIcon": s.badgeIcon,
        "features": s.features or [],
        "billingCycles": _plan_cycles(s),
    } for s in qs]
    out = {"items": items, "total": len(items)}
    # Assemble the family compare table from per-plan compareRows columns
    # (dedup by tag — a multi-cycle plan stores the same column on every row).
    cols, seen = [], set()
    for s in qs:
        if s.compareRows and s.tag and s.tag not in seen:
            seen.add(s.tag)
            cols.append(s.compareRows)
    if cols:
        labels = [v.get("feature", "") for v in cols[0].get("values", [])]
        out["compare"] = {
            "columns": [c.get("column", "") for c in cols],
            # Index within the full table including the frontend's static
            # "Feature" header column (CompareTableContent semantics).
            "popularColIndex": next(
                (i + 1 for i, c in enumerate(cols) if c.get("popular")), 0),
            "rows": [{
                "feature": label,
                "values": [
                    next((v.get("value", "") for v in c.get("values", [])
                          if v.get("feature") == label), "")
                    for c in cols
                ],
            } for label in labels],
        }
    return out


# ---------------------------------------------------------------------------
# 15. resolve/<entityType>/<slug>/ — public slug → {entityType, id, slug, name}
# ---------------------------------------------------------------------------
_RESOLVE_VALID_TYPES = set(ENTITY_TYPE.ALL)


def resolve_entity(entity_type, slug):
    """Look up any entity by entityType + slug.  Returns minimal identity dict."""
    if entity_type not in _RESOLVE_VALID_TYPES:
        raise NotFound_(f"unknown entityType '{entity_type}'")
    try:
        model = get_model(entity_type)
    except KeyError:
        raise NotFound_(f"unknown entityType '{entity_type}'")

    obj = model.objects.filter(slug=slug).first()
    if not obj:
        raise NotFound_(f"{entity_type} with slug '{slug}' not found")

    # Determine display name per entity type
    if entity_type == ENTITY_TYPE.BUSINESS:
        name = getattr(obj, "businessName", "") or str(obj)
    else:
        # Shop/Architect → .name; Product/Service/Catelogue → .title
        name = getattr(obj, "name", None) or getattr(obj, "title", "") or str(obj)

    return {
        "entityType": entity_type,
        "id": obj.id,
        "slug": obj.slug,
        "name": name,
    }


# ---------------------------------------------------------------------------
# 16. Credential CRUD — Award + ProcessStep + Expertise (Phase 1)
# ---------------------------------------------------------------------------
# Ownership helpers:
#   business → business.user_id == user.id (Business has .user OneToOne)
#   shop     → shop.user_id == user.id
#   architect → architect.user_id == user.id

_CRED_ENTITY_FK = {
    ENTITY_TYPE.ARCHITECT: "architect",
    ENTITY_TYPE.SHOP: "shop",
    ENTITY_TYPE.BUSINESS: "business",
}

_ENTITY_OWNER_TYPES = {ENTITY_TYPE.ARCHITECT, ENTITY_TYPE.SHOP, ENTITY_TYPE.BUSINESS}


def _resolve_owner_entity(user, entity_type, entity_id):
    """Resolve entity by (entityType, entityId) and verify the requesting user owns it.
    Reuses the same ownership pattern as update_shop / update_architect in CrudController:
    - Architect.user == user (OneToOneField via related_name 'user_architect')
    - Shop.user == user (ForeignKey, user can own multiple shops)
    - Business.user == user (OneToOneField via related_name 'user_business')
    Raises NotFound_ or PermissionError_ on failure.
    Returns (entity, fk_name).
    """
    if entity_type not in _ENTITY_OWNER_TYPES:
        raise NotFound_(f"unsupported entityType '{entity_type}'")
    model = get_model(entity_type)
    obj = model.objects.filter(id=entity_id).first()
    if not obj:
        raise NotFound_(f"{entity_type} not found")
    owner_id = getattr(obj, "user_id", None)
    if owner_id != user.id:
        raise PermissionError_(f"not the {entity_type} owner")
    return obj, _CRED_ENTITY_FK[entity_type]


# ---- Award ----

def create_award(user, payload):
    from app_ib.engine_models import Award
    entity_type = (payload.get("entityType") or "").strip()
    entity_id = payload.get("entityId")
    title = (payload.get("title") or "").strip()
    if not entity_type or not entity_id or not title:
        raise ValueError("entityType, entityId and title are required")
    try:
        entity_id = int(entity_id)
    except (TypeError, ValueError):
        raise ValueError("entityId must be an integer")
    entity, fk = _resolve_owner_entity(user, entity_type, entity_id)
    kind = (payload.get("kind") or "award").strip()
    if kind not in ("award", "credential"):
        kind = "award"
    award = Award.objects.create(
        **{fk: entity},
        title=title,
        issuer=payload.get("issuer") or "",
        year=str(payload.get("year") or ""),
        description=payload.get("description") or "",
        imageUrl=payload.get("imageUrl") or "",
        kind=kind,
        index=int(payload.get("index") or 0),
        isActive=True,
    )
    return _award_row(award)


def update_award(user, award_id, payload):
    from app_ib.engine_models import Award
    award = Award.objects.select_related("architect", "shop", "business").filter(id=award_id).first()
    if not award:
        raise NotFound_("award not found")
    # resolve owning entity and verify ownership
    if award.architect_id:
        _resolve_owner_entity(user, ENTITY_TYPE.ARCHITECT, award.architect_id)
    elif award.shop_id:
        _resolve_owner_entity(user, ENTITY_TYPE.SHOP, award.shop_id)
    elif award.business_id:
        _resolve_owner_entity(user, ENTITY_TYPE.BUSINESS, award.business_id)
    else:
        raise PermissionError_("award has no owner")
    updatable = ("title", "issuer", "description", "imageUrl", "kind", "index", "isActive")
    for field in updatable:
        if field in payload and payload[field] is not None:
            setattr(award, field, payload[field])
    if "year" in payload and payload["year"] is not None:
        award.year = str(payload["year"])
    if "kind" in payload and award.kind not in ("award", "credential"):
        award.kind = "award"
    award.save()
    return _award_row(award)


def delete_award(user, award_id):
    from app_ib.engine_models import Award
    award = Award.objects.select_related("architect", "shop", "business").filter(id=award_id).first()
    if not award:
        raise NotFound_("award not found")
    if award.architect_id:
        _resolve_owner_entity(user, ENTITY_TYPE.ARCHITECT, award.architect_id)
    elif award.shop_id:
        _resolve_owner_entity(user, ENTITY_TYPE.SHOP, award.shop_id)
    elif award.business_id:
        _resolve_owner_entity(user, ENTITY_TYPE.BUSINESS, award.business_id)
    else:
        raise PermissionError_("award has no owner")
    # soft-delete (mirror how CrudController.delete_review uses isDeleted=True)
    award.isActive = False
    award.save(update_fields=["isActive"])
    return True


# ---- ProcessStep ----

def _step_row(p):
    return {
        "id": p.id,
        "stepNumber": p.stepNumber,
        "title": p.title,
        "description": p.description,
    }


def create_process_step(user, payload):
    from app_ib.engine_models import ProcessStep
    entity_type = (payload.get("entityType") or "").strip()
    entity_id = payload.get("entityId")
    title = (payload.get("title") or "").strip()
    if not entity_type or not entity_id or not title:
        raise ValueError("entityType, entityId and title are required")
    try:
        entity_id = int(entity_id)
    except (TypeError, ValueError):
        raise ValueError("entityId must be an integer")
    entity, fk = _resolve_owner_entity(user, entity_type, entity_id)
    step = ProcessStep.objects.create(
        **{fk: entity},
        stepNumber=int(payload.get("stepNumber") or 0),
        title=title,
        description=payload.get("description") or "",
        index=int(payload.get("index") or 0),
        isActive=True,
    )
    return _step_row(step)


def update_process_step(user, step_id, payload):
    from app_ib.engine_models import ProcessStep
    step = ProcessStep.objects.select_related("architect", "shop", "business").filter(id=step_id).first()
    if not step:
        raise NotFound_("process step not found")
    if step.architect_id:
        _resolve_owner_entity(user, ENTITY_TYPE.ARCHITECT, step.architect_id)
    elif step.shop_id:
        _resolve_owner_entity(user, ENTITY_TYPE.SHOP, step.shop_id)
    elif step.business_id:
        _resolve_owner_entity(user, ENTITY_TYPE.BUSINESS, step.business_id)
    else:
        raise PermissionError_("process step has no owner")
    for field in ("title", "description", "stepNumber", "index", "isActive"):
        if field in payload and payload[field] is not None:
            setattr(step, field, payload[field])
    step.save()
    return _step_row(step)


def delete_process_step(user, step_id):
    from app_ib.engine_models import ProcessStep
    step = ProcessStep.objects.select_related("architect", "shop", "business").filter(id=step_id).first()
    if not step:
        raise NotFound_("process step not found")
    if step.architect_id:
        _resolve_owner_entity(user, ENTITY_TYPE.ARCHITECT, step.architect_id)
    elif step.shop_id:
        _resolve_owner_entity(user, ENTITY_TYPE.SHOP, step.shop_id)
    elif step.business_id:
        _resolve_owner_entity(user, ENTITY_TYPE.BUSINESS, step.business_id)
    else:
        raise PermissionError_("process step has no owner")
    step.isActive = False
    step.save(update_fields=["isActive"])
    return True


# ---- Expertise (Tag M2M set) ----

def set_expertise(user, payload):
    from app_ib.engine_models import Tag
    entity_type = (payload.get("entityType") or "").strip()
    entity_id = payload.get("entityId")
    tags_input = payload.get("tags") or []
    if not entity_type or not entity_id:
        raise ValueError("entityType and entityId are required")
    try:
        entity_id = int(entity_id)
    except (TypeError, ValueError):
        raise ValueError("entityId must be an integer")
    if not isinstance(tags_input, list):
        raise ValueError("tags must be a list of strings")
    entity, _ = _resolve_owner_entity(user, entity_type, entity_id)
    tags = []
    for text in tags_input:
        text = str(text).strip()
        if text:
            tag = Tag.getOrCreateFromText(text)
            if tag:
                tags.append(tag)
    entity.expertiseTags.set(tags)
    return {"expertise": [t.value for t in tags]}


# ---------------------------------------------------------------------------
# 17. recently-viewed/summary/ — aggregate over user's RecentlyViewed rows
# ---------------------------------------------------------------------------

def recently_viewed_summary(user):
    """Return facets, KPIs, and the single most-recent hydrated row (continue banner).

    Shape:
    {
        facets: [{entityType, count}, ...],   # grouped by entityType
        kpis: {total, thisWeek, uniqueTypes},
        continue: {entityType, objectId, name, imageUrl, slug, viewedAt} | null
    }
    """
    from app_ib.engine_models import RecentlyViewed
    from app_ib.Controllers.Engine.EngineController import _name, _image
    from django.db.models import Count as _Count

    now = timezone.now()
    week_ago = now - timedelta(days=7)

    qs = RecentlyViewed.objects.filter(user=user).select_related("contentType")
    rows = list(qs.order_by("-viewedAt"))

    total = len(rows)
    this_week = sum(1 for r in rows if r.viewedAt and r.viewedAt >= week_ago)

    # facet by entityType (contentType.model)
    facet_map = {}
    for r in rows:
        et = r.contentType.model if r.contentType_id else ""
        facet_map[et] = facet_map.get(et, 0) + 1
    facets = sorted(
        [{"entityType": et, "count": cnt} for et, cnt in facet_map.items()],
        key=lambda x: -x["count"]
    )
    unique_types = len(facet_map)

    # hydrate the single most-recent row for the "continue" banner
    continue_item = None
    for r in rows:
        if not r.contentType_id:
            continue
        model_class = r.contentType.model_class()
        if model_class is None:
            continue
        obj = model_class.objects.filter(id=r.objectId).first()
        if obj:
            continue_item = {
                "entityType": r.contentType.model,
                "objectId": r.objectId,
                "name": _name(obj),
                "imageUrl": _image(obj),
                "slug": getattr(obj, "slug", "") or "",
                "viewedAt": r.viewedAt.isoformat() if r.viewedAt else None,
            }
            break

    return {
        "facets": facets,
        "kpis": {
            "total": total,
            "thisWeek": this_week,
            "uniqueTypes": unique_types,
        },
        "continue": continue_item,
    }


# ---------------------------------------------------------------------------
# Phase 2 — UserSession endpoints
# ---------------------------------------------------------------------------

def my_sessions(user, current_jti=None):
    """Return active (non-revoked) sessions for the user, newest first.

    current_jti — the sjti claim from the caller's access token; used to flag
    the session the request is being made FROM as isCurrent=True.

    Shape:
      { items: [{id, deviceLabel, userAgent, ipAddress, city,
                 lastActiveAt, createdAt, isCurrent}], total }
    """
    from app_ib.engine_models import UserSession
    from app_ib.Utils.Names import NAMES as _N

    qs = (UserSession.objects
          .filter(user=user, revokedAt__isnull=True)
          .order_by("-lastActiveAt"))

    items = []
    for s in qs:
        items.append({
            _N.ID: s.id,
            _N.DEVICE_LABEL: s.deviceLabel,
            _N.USER_AGENT: s.userAgent,
            _N.IP_ADDRESS: s.ipAddress,
            _N.CITY: s.city,
            _N.LAST_ACTIVE_AT: s.lastActiveAt.isoformat() if s.lastActiveAt else None,
            _N.CREATED_AT: s.createdAt.isoformat() if s.createdAt else None,
            _N.IS_CURRENT: (s.jti == current_jti) if current_jti else False,
        })

    return {
        _N.ITEMS: items,
        _N.TOTAL: len(items),
    }


def revoke_session(user, session_id):
    """Revoke a single session owned by the user.

    Sets revokedAt; best-effort blacklists the associated refresh token via
    the token_blacklist app (OutstandingToken → BlacklistedToken).

    Shape: { revoked: true, id: <session_id> }
    """
    from app_ib.engine_models import UserSession
    from app_ib.Utils.Names import NAMES as _N

    session = UserSession.objects.filter(id=session_id, user=user).first()
    if not session:
        raise NotFound_("session not found")
    if session.revokedAt is not None:
        # Already revoked — idempotent
        return {_N.REVOKED: True, _N.ID: session_id}

    session.revokedAt = timezone.now()
    session.save(update_fields=["revokedAt"])

    # Best-effort: blacklist the outstanding refresh token by jti
    _blacklist_jti(session.jti)

    return {_N.REVOKED: True, _N.ID: session_id}


def revoke_all_other_sessions(user, current_jti=None):
    """Revoke every active session for the user EXCEPT the caller's current one
    (task 81 — "Sign out everywhere"). Blacklists each revoked session's refresh
    token best-effort. Shape: { revoked: <count> }."""
    from app_ib.engine_models import UserSession
    qs = UserSession.objects.filter(user=user, revokedAt__isnull=True)
    if current_jti:
        qs = qs.exclude(jti=current_jti)
    sessions = list(qs)
    now = timezone.now()
    for s in sessions:
        s.revokedAt = now
        s.save(update_fields=["revokedAt"])
        _blacklist_jti(s.jti)
    return {"revoked": len(sessions)}


def _blacklist_jti(jti: str) -> None:
    """Look up the OutstandingToken by jti and blacklist it. Non-fatal."""
    if not jti:
        return
    try:
        from rest_framework_simplejwt.token_blacklist.models import (
            OutstandingToken,
            BlacklistedToken,
        )
        ot = OutstandingToken.objects.filter(jti=jti).first()
        if ot:
            BlacklistedToken.objects.get_or_create(token=ot)
    except Exception as exc:
        logger.warning("_blacklist_jti failed (non-fatal) jti=%s: %s", jti[:12], exc)


# ---------------------------------------------------------------------------
# Phase 3 — 1. Related items
# ---------------------------------------------------------------------------
def _card_for(entity_type, obj):
    """Compact card dict for a target entity (reuses existing _name/_image helpers)."""
    from app_ib.Controllers.Engine.EngineController import _name, _image
    card = {
        "entityType": entity_type,
        "id": obj.id,
        "slug": getattr(obj, "slug", "") or "",
        "name": _name(obj),
        "imageUrl": _image(obj),
    }
    # For product/service include displayPrice if present
    price = getattr(obj, "displayPrice", None)
    if price is not None:
        card["displayPrice"] = price
    return card


def related_items(entity_type, object_id, limit=12):
    """Pre-computed co-view related items with live fallback.

    Shape: { items: [...], total: int, source: {entityType, id} }
    Each item: { entityType, id, slug, name, imageUrl, displayPrice? }
    """
    from app_ib.engine_models import RelatedItem
    from app_ib.algorithms.helpers import get_model, content_type_for, ENTITY_MODELS
    from app_ib.Utils.Names import NAMES as _N

    # Validate entity type
    if entity_type not in ENTITY_MODELS:
        raise NotFound_(f"unknown entityType: {entity_type}")

    source_ct = content_type_for(entity_type)
    source_model = get_model(entity_type)

    # Verify source exists
    if not source_model.objects.filter(id=object_id).exists():
        raise NotFound_(f"{entity_type} {object_id} not found")

    # --- Primary: stored RelatedItem rows ---
    rows = (RelatedItem.objects
            .filter(sourceContentType=source_ct, sourceObjectId=object_id)
            .select_related("targetContentType")
            .order_by("-score")[:limit])

    items = []
    seen_pairs = set()  # (contentType_id, objectId)
    seen_pairs.add((source_ct.id, object_id))  # exclude source itself

    for row in rows:
        tc = row.targetContentType
        oid = row.targetObjectId
        if (tc.id, oid) in seen_pairs:
            continue
        model_cls = tc.model_class()
        if model_cls is None:
            continue
        obj = model_cls.objects.filter(id=oid).first()
        if not obj:
            continue
        # Exclude inactive objects
        if not getattr(obj, "isActive", True):
            continue
        seen_pairs.add((tc.id, oid))
        card = _card_for(tc.model, obj)
        card["reason"] = row.reason
        items.append(card)

    # --- Fallback: fill up to limit with live data ---
    if len(items) < limit:
        needed = limit - len(items)
        fallback = _related_fallback(entity_type, object_id, needed, seen_pairs)
        items.extend(fallback)

    return {
        _N.ITEMS: items,
        _N.TOTAL: len(items),
        _N.SOURCE: {_N.ENTITY_TYPE: entity_type, _N.ID: object_id},
    }


def _related_fallback(entity_type, object_id, needed, seen_pairs):
    """Live fallback: same-category items then top trending of that type."""
    from app_ib.Utils.EngineConfig import ENTITY_TYPE
    from app_ib.algorithms.helpers import content_type_for

    fallback_items = []

    try:
        if entity_type == ENTITY_TYPE.PRODUCT:
            from interior_products.models import Product
            src = Product.objects.filter(id=object_id).prefetch_related("category").first()
            if src:
                cat_ids = list(src.category.values_list("id", flat=True))
                src_ct_id = content_type_for(ENTITY_TYPE.PRODUCT).id
                qs = (Product.objects
                      .filter(isActive=True, category__id__in=cat_ids)
                      .exclude(id=object_id)
                      .order_by("-trendingScore", "-viewCount")
                      .distinct())
                for obj in qs[:needed + 20]:
                    if (src_ct_id, obj.id) in seen_pairs:
                        continue
                    seen_pairs.add((src_ct_id, obj.id))
                    fallback_items.append(_card_for(ENTITY_TYPE.PRODUCT, obj))
                    if len(fallback_items) >= needed:
                        break

        elif entity_type == ENTITY_TYPE.SERVICE:
            from interior_products.models import Service
            src = Service.objects.filter(id=object_id).prefetch_related("category").first()
            if src:
                cat_ids = list(src.category.values_list("id", flat=True))
                src_ct_id = content_type_for(ENTITY_TYPE.SERVICE).id
                qs = (Service.objects
                      .filter(isActive=True, category__id__in=cat_ids)
                      .exclude(id=object_id)
                      .order_by("-trendingScore", "-viewCount")
                      .distinct())
                for obj in qs[:needed + 20]:
                    if (src_ct_id, obj.id) in seen_pairs:
                        continue
                    seen_pairs.add((src_ct_id, obj.id))
                    fallback_items.append(_card_for(ENTITY_TYPE.SERVICE, obj))
                    if len(fallback_items) >= needed:
                        break

        elif entity_type in (ENTITY_TYPE.BUSINESS, ENTITY_TYPE.SHOP, ENTITY_TYPE.ARCHITECT):
            from app_ib.models import Business
            src_ct_id = content_type_for(entity_type).id
            # Location-based: businesses in same city
            from app_ib.algorithms.helpers import get_model
            model = get_model(entity_type)
            src = model.objects.filter(id=object_id).first()
            city = getattr(src, "city", "") or ""
            if entity_type == ENTITY_TYPE.BUSINESS:
                city = _business_city(src) if src else ""
            if city:
                qs = model.objects.filter(isActive=True).exclude(id=object_id)
                if entity_type == ENTITY_TYPE.BUSINESS:
                    qs = qs.filter(business_location__city__icontains=city)
                else:
                    qs = qs.filter(city__icontains=city)
                qs = qs.order_by("-trendingScore")
                for obj in qs[:needed + 20]:
                    if (src_ct_id, obj.id) in seen_pairs:
                        continue
                    seen_pairs.add((src_ct_id, obj.id))
                    fallback_items.append(_card_for(entity_type, obj))
                    if len(fallback_items) >= needed:
                        break

    except Exception:
        pass

    # Still need more? Top trending of same type
    if len(fallback_items) < needed:
        still_need = needed - len(fallback_items)
        try:
            from app_ib.models import TrendingScore
            from app_ib.Utils.EngineConfig import TRENDING_PERIOD
            from app_ib.algorithms.helpers import content_type_for, get_model
            ct = content_type_for(entity_type)
            rows = (TrendingScore.objects
                    .filter(contentType=ct, period=TRENDING_PERIOD.WEEKLY, city="")
                    .order_by("rank")[:still_need + 20])
            model = get_model(entity_type)
            objs = {o.id: o for o in model.objects.filter(id__in=[r.objectId for r in rows])}
            for r in rows:
                obj = objs.get(r.objectId)
                if not obj:
                    continue
                if not getattr(obj, "isActive", True):
                    continue
                if (ct.id, obj.id) in seen_pairs:
                    continue
                seen_pairs.add((ct.id, obj.id))
                fallback_items.append(_card_for(entity_type, obj))
                if len(fallback_items) >= needed:
                    break
        except Exception:
            pass

    return fallback_items[:needed]


# ---------------------------------------------------------------------------
# Phase 3 — 2. Newsletter subscribe
# ---------------------------------------------------------------------------
def newsletter_subscribe(email, source="blog", user=None):
    """Idempotent newsletter subscription.

    Shape: { subscribed: true, alreadySubscribed: bool, email: str }
    `alreadySubscribed` is True when the email was already an active subscriber, so
    the UI can show "you're already subscribed" instead of a fresh "subscribed!".
    """
    import re
    from app_ib.models import NewsletterSubscriber
    from app_ib.Utils.Names import NAMES as _N
    from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES

    # Simple email validation
    if not email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email.strip()):
        raise ValueError(RESPONSE_MESSAGES.invalid_email)

    email = email.strip().lower()

    obj, created = NewsletterSubscriber.objects.get_or_create(
        email=email,
        defaults={
            "source": source or "blog",
            "user": user,
            "isActive": True,
        },
    )
    already = bool(not created and obj.isActive)
    if not created and not obj.isActive:
        # Re-activate a previously-unsubscribed email (treated as a fresh subscribe).
        obj.isActive = True
        obj.save(update_fields=["isActive"])

    return {_N.SUBSCRIBED: True, "alreadySubscribed": already, _N.EMAIL: email}


# ---------------------------------------------------------------------------
# Phase 3 — 3. Blog featured
# ---------------------------------------------------------------------------
def featured_blogs(limit=1):
    """Return featured Blog rows.

    Shape: { items: [{id, title, slug, coverImageUrl, author, authorImageUrl, timestamp}] }
    """
    from app_ib.models import Blog
    from app_ib.Utils.Names import NAMES as _N

    qs = (Blog.objects
          .filter(isFeatured=True, status="published")
          .order_by("featuredOrder", "-timestamp")[:limit])

    items = []
    for b in qs:
        item = {
            _N.ID: b.id,
            _N.TITLE: b.title or "",
            _N.SLUG: b.slug or "",
            _N.COVER_IMAGE_URL: b.coverImageUrl or "",
            _N.AUTHOR: b.author or "",
            _N.AUTHOR_IMAGE_URL: b.authorImageUrl or "",
            _N.TIMESTAMP: b.timestamp.isoformat() if b.timestamp else None,
        }
        # Best-effort plain excerpt from QuillField (description.html → strip tags)
        try:
            import re as _re
            html = b.description.html if b.description else ""
            text = _re.sub(r"<[^>]+>", " ", html or "")
            text = " ".join(text.split())
            if text:
                item[_N.EXCERPT] = text[:300]
        except Exception:
            pass
        items.append(item)

    return {_N.ITEMS: items}


# ---------------------------------------------------------------------------
# Phase 3 — 4. Catalogue trending
# ---------------------------------------------------------------------------
def trending_catalogues(period="", city="", limit=12):
    """Top catalogues by trendingScore then viewCount.

    Shape: { items: [{id, slug, name, imageUrl, businessName, viewCount}] }
    """
    from interior_products.models import Catelogue
    from app_ib.Utils.Names import NAMES as _N

    try:
        limit = max(1, min(int(limit), 50))
    except (ValueError, TypeError):
        limit = 12

    qs = (Catelogue.objects
          .select_related("business", "business__business_location")
          .filter(isActive=True)
          .order_by("-trendingScore", "-viewCount", "-createdAt"))

    if city:
        qs = qs.filter(business__business_location__city__icontains=city)

    items = []
    for c in qs[:limit]:
        items.append({
            _N.ID: c.id,
            _N.SLUG: c.slug or "",
            _N.NAME: c.title or "",
            _N.IMAGE_URL: c.catelougeImage or "",
            _N.BUSINESS_NAME: (c.business.businessName if c.business_id and c.business else ""),
            _N.VIEW_COUNT: c.viewCount,
            _N.TRENDING_SCORE: c.trendingScore,
        })

    return {_N.ITEMS: items}


# ---------------------------------------------------------------------------
# Phase 3 — 5. Engine my/profile/
# ---------------------------------------------------------------------------
def update_my_profile(user, data):
    """PATCH my/profile/ — persist name/phone/city from the Settings account form (F13)."""
    from app_ib.models import UserProfile, Location
    name = (data.get("name") or "").strip()
    phone = (data.get("phone") or "").strip()
    city = (data.get("city") or "").strip()
    try:
        profile = user.user_profile
        if name:
            profile.name = name
        if phone:
            profile.phone = phone
        profile.save(update_fields=["name", "phone"])
    except Exception:
        pass
    if city:
        try:
            loc = user.user_location
            loc.city = city
            loc.save(update_fields=["city"])
        except Exception:
            pass


def my_profile(user):
    """Engine profile for the authenticated user.

    Shape: { id, name, email, phone, countryCode, role, city,
             isVerified, profileImageUrl }
    """
    from app_ib.models import UserProfile, Location
    from app_ib.Utils.Names import NAMES as _N

    profile = None
    try:
        profile = user.user_profile
    except Exception:
        pass

    city = ""
    try:
        loc = user.user_location
        city = loc.city or ""
    except Exception:
        pass

    return {
        _N.ID: user.id,
        _N.NAME: (profile.name if profile else "") or "",
        _N.EMAIL: (profile.email if profile else user.username) or "",
        _N.PHONE: (profile.phone if profile else "") or "",
        _N.COUNTRY_CODE: (profile.countryCode if profile else "") or "",
        _N.ROLE: user.type or "",
        _N.CITY: city,
        _N.IS_VERIFIED: user.isVerified,
        _N.PROFILE_IMAGE_URL: (profile.profileImageUrl if profile else "") or "",
    }


# ==========================================================================
# my/change-password/ — authenticated password change for the v3 dashboard
# ==========================================================================
def change_password(user, payload):
    """Change the authenticated user's password.

    Verifies the supplied current password against the stored hash (same check
    the login flow uses) before setting the new one. v3-only — does not touch
    the legacy auth change-password / reset-password endpoints.

    payload: { currentPassword, newPassword, confirmPassword }
    Returns: {} on success. Raises ValueError on bad input / wrong current pwd.
    """
    from django.contrib.auth.hashers import check_password, make_password

    current = (payload.get("currentPassword") or "").strip()
    new = payload.get("newPassword") or ""
    confirm = payload.get("confirmPassword") or ""

    if not current or not new or not confirm:
        raise ValueError("currentPassword, newPassword and confirmPassword are required")
    if new != confirm:
        raise ValueError("New password and confirmation do not match")
    if len(new) < 8:
        raise ValueError("New password must be at least 8 characters")
    if not check_password(current, user.password):
        raise ValueError("Current password is incorrect")

    user.password = make_password(new)
    user.save()  # full save — mirrors AuthTasks.ChangePassword precedent
    return {}
