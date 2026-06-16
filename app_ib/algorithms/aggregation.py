"""Aggregation algorithms (background jobs):
 11. Rating Aggregation        recompute_ratings()
 13. Daily Analytics           aggregate_daily_analytics()
 22. Average Response Time     compute_avg_response()
 10. Trending Searches         calculate_trending_searches()
  9. City Pulse                compute_city_pulse()
 12. Daily Discovery Lists     compute_daily_discovery_lists()
"""
from collections import defaultdict
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Avg, F

from app_ib.Utils.SafeCache import safe_cache as cache
from app_ib.Utils.EngineConfig import ENTITY_TYPE, CLICK_TYPE, ALGO
from app_ib.algorithms.helpers import get_model, content_type_for


# ---------------------------------------------------------------------------
# 11. Rating Aggregation — daily; breakdown percentages sum to exactly 100
# ---------------------------------------------------------------------------
def recompute_ratings():
    from app_ib.models import Review
    updated = 0
    fk_by_entity = {
        ENTITY_TYPE.BUSINESS: "business", ENTITY_TYPE.SHOP: "shop",
        ENTITY_TYPE.PRODUCT: "product", ENTITY_TYPE.SERVICE: "service",
        ENTITY_TYPE.ARCHITECT: "architect",
    }
    # Business/Product/Service keep a legacy CharField `rating`, so the float lives
    # in `ratingValue`. Shop/Architect have no legacy field and use `rating`.
    rating_field_by_entity = {
        ENTITY_TYPE.BUSINESS: "ratingValue", ENTITY_TYPE.PRODUCT: "ratingValue",
        ENTITY_TYPE.SERVICE: "ratingValue", ENTITY_TYPE.SHOP: "rating",
        ENTITY_TYPE.ARCHITECT: "rating",
    }
    for entity_type in ENTITY_TYPE.RATED:
        model = get_model(entity_type)
        fk = fk_by_entity[entity_type]
        rf = rating_field_by_entity[entity_type]
        fields = [rf, "totalReviews", "ratingBreakdown"]
        for obj in model.objects.all():
            reviews = Review.objects.filter(**{fk: obj, "isDeleted": False, "isApproved": True})
            total = reviews.count()
            if total == 0:
                setattr(obj, rf, 0.0)
                obj.totalReviews, obj.ratingBreakdown = 0, {}
                obj.save(update_fields=fields)
                continue
            star_counts = {i: 0 for i in range(1, 6)}
            score_sum = 0
            for r in reviews.values("rating"):
                star = max(1, min(5, r["rating"]))
                star_counts[star] += 1
                score_sum += star
            setattr(obj, rf, round(score_sum / total, 2))
            obj.totalReviews = total
            obj.ratingBreakdown = _percent_breakdown(star_counts, total)
            obj.save(update_fields=fields)
            updated += 1
    return updated


def _percent_breakdown(star_counts, total):
    """Percentages summing to exactly 100 (largest-remainder rounding)."""
    raw = {s: (c * 100.0 / total) for s, c in star_counts.items()}
    floored = {s: int(v) for s, v in raw.items()}
    remainder = 100 - sum(floored.values())
    # distribute the remaining points to the largest fractional parts
    order = sorted(star_counts, key=lambda s: raw[s] - floored[s], reverse=True)
    for s in order[:remainder]:
        floored[s] += 1
    return {f"{s}_star": floored[s] for s in range(5, 0, -1)}


# ---------------------------------------------------------------------------
# 13. Daily Analytics Aggregation — one row per entity per date
# ---------------------------------------------------------------------------
def aggregate_daily_analytics(for_date=None):
    from app_ib.models import (ViewEvent, ClickEvent, SavedItem, LeadQuery,
                               BusinessAnalytics)
    day = for_date or (timezone.now().date() - timedelta(days=0))
    start = timezone.make_aware(timezone.datetime(day.year, day.month, day.day))
    end = start + timedelta(days=1)
    written = 0

    for entity_type in (ENTITY_TYPE.BUSINESS, ENTITY_TYPE.SHOP, ENTITY_TYPE.ARCHITECT):
        model = get_model(entity_type)
        ct = content_type_for(entity_type)

        views = defaultdict(int); uniques = defaultdict(set)
        for v in ViewEvent.objects.filter(contentType=ct, timestamp__gte=start, timestamp__lt=end) \
                .values("objectId", "user_id", "sessionId"):
            views[v["objectId"]] += 1
            uniques[v["objectId"]].add(v["user_id"] or f"s:{v['sessionId']}")

        wa = defaultdict(int); call = defaultdict(int)
        for c in ClickEvent.objects.filter(contentType=ct, timestamp__gte=start, timestamp__lt=end) \
                .values("objectId", "clickType"):
            if c["clickType"] == CLICK_TYPE.WHATSAPP:
                wa[c["objectId"]] += 1
            elif c["clickType"] == CLICK_TYPE.CALL:
                call[c["objectId"]] += 1

        saves = defaultdict(int)
        for s in SavedItem.objects.filter(contentType=ct, timestamp__gte=start, timestamp__lt=end) \
                .values("objectId"):
            saves[s["objectId"]] += 1

        leads = defaultdict(int); quotes = defaultdict(int)
        if entity_type == ENTITY_TYPE.BUSINESS:
            for l in LeadQuery.objects.filter(business__isnull=False, timestamp__gte=start, timestamp__lt=end) \
                    .values("business_id", "formType"):
                leads[l["business_id"]] += 1
                if l["formType"] == "quote":
                    quotes[l["business_id"]] += 1

        obj_ids = set(views) | set(wa) | set(call) | set(saves) | set(leads)
        for oid in obj_ids:
            BusinessAnalytics.objects.update_or_create(
                contentType=ct, objectId=oid, date=day,
                defaults={
                    "viewCount": views.get(oid, 0),
                    "uniqueVisitorCount": len(uniques.get(oid, set())),
                    "leadCount": leads.get(oid, 0),
                    "quoteCount": quotes.get(oid, 0),
                    "whatsappTapCount": wa.get(oid, 0),
                    "callTapCount": call.get(oid, 0),
                    "saveCount": saves.get(oid, 0),
                },
            )
            written += 1
        _compute_enquiry_growth(ct, day)
    return written


def _compute_enquiry_growth(ct, day):
    """enquiryGrowthPct = today's leadCount vs previous day, per entity."""
    from app_ib.models import BusinessAnalytics
    prev = day - timedelta(days=1)
    prev_map = {r["objectId"]: r["leadCount"] for r in
                BusinessAnalytics.objects.filter(contentType=ct, date=prev).values("objectId", "leadCount")}
    for row in BusinessAnalytics.objects.filter(contentType=ct, date=day):
        before = prev_map.get(row.objectId, 0)
        if before > 0:
            row.enquiryGrowthPct = round((row.leadCount - before) * 100.0 / before, 2)
        elif row.leadCount > 0:
            row.enquiryGrowthPct = 100.0
        else:
            row.enquiryGrowthPct = 0.0
        row.save(update_fields=["enquiryGrowthPct"])


# ---------------------------------------------------------------------------
# 22. Average Response Time — rolling 30 days; lower is better
# ---------------------------------------------------------------------------
def compute_avg_response():
    from app_ib.models import LeadQuery
    cutoff = timezone.now() - timedelta(days=ALGO.AVG_RESPONSE_WINDOW_DAYS)
    updated = 0
    # business only (LeadQuery FK)
    model = get_model(ENTITY_TYPE.BUSINESS)
    rows = (LeadQuery.objects.filter(business__isnull=False, respondedAt__isnull=False,
                                     timestamp__gte=cutoff)
            .annotate(delta=F("respondedAt") - F("timestamp")))
    sums = defaultdict(lambda: [0.0, 0])
    for r in rows:
        secs = (r.respondedAt - r.timestamp).total_seconds()
        if secs < 0:
            continue
        agg = sums[r.business_id]
        agg[0] += secs; agg[1] += 1
    for biz in model.objects.all():
        agg = sums.get(biz.id)
        biz.avgResponseSeconds = int(agg[0] / agg[1]) if agg and agg[1] else None
        biz.save(update_fields=["avgResponseSeconds"])
        updated += 1
    return updated


# ---------------------------------------------------------------------------
# 10. Trending Searches — top 20, 24h window, min 5 occurrences
# ---------------------------------------------------------------------------
def calculate_trending_searches():
    from app_ib.models import SearchEvent
    cutoff = timezone.now() - timedelta(hours=ALGO.TRENDING_SEARCH_WINDOW_HOURS)
    rows = (SearchEvent.objects.filter(timestamp__gte=cutoff)
            .values("normalizedQuery").annotate(c=Count("id")).order_by("-c"))
    board = [{"query": r["normalizedQuery"], "count": r["c"]}
             for r in rows if r["c"] >= ALGO.TRENDING_SEARCH_MIN_COUNT][:ALGO.TRENDING_SEARCH_TOP_N]
    cache.set("trending:searches:24h", board, ALGO.TRENDING_SEARCH_TTL_SECONDS)
    return board


# ---------------------------------------------------------------------------
# 9. City Pulse — per city: top businesses (TrendingScore) + top searches
# ---------------------------------------------------------------------------
def compute_city_pulse():
    from app_ib.models import TrendingScore, SearchEvent, Business
    from app_ib.Utils.EngineConfig import TRENDING_PERIOD
    ct = content_type_for(ENTITY_TYPE.BUSINESS)
    cutoff = timezone.now() - timedelta(hours=24)
    cities = set(SearchEvent.objects.filter(timestamp__gte=cutoff)
                 .exclude(city="").values_list("city", flat=True))
    cities |= set(TrendingScore.objects.filter(contentType=ct).exclude(city="")
                  .values_list("city", flat=True))
    payloads = {}
    for city in cities:
        top_biz_rows = (TrendingScore.objects.filter(contentType=ct, period=TRENDING_PERIOD.DAILY, city=city)
                        .order_by("-score")[:ALGO.CITY_PULSE_TOP_BUSINESSES])
        biz_map = {b.id: b for b in Business.objects.filter(
            id__in=[r.objectId for r in top_biz_rows])}
        top_businesses = []
        for r in top_biz_rows:
            b = biz_map.get(r.objectId)
            if b:
                top_businesses.append({"id": b.id, "name": b.businessName,
                                       "slug": b.slug, "trendingScore": r.score})
        top_searches = [
            {"query": x["normalizedQuery"], "count": x["c"]}
            for x in (SearchEvent.objects.filter(timestamp__gte=cutoff, city=city)
                      .values("normalizedQuery").annotate(c=Count("id")).order_by("-c")[:ALGO.CITY_PULSE_TOP_SEARCHES])
        ]
        payload = {"city": city, "updated_at": timezone.now().isoformat(),
                   "top_businesses": top_businesses, "trending_searches": top_searches}
        cache.set(f"city_pulse:{city}", payload, ALGO.CITY_PULSE_TTL_SECONDS)
        payloads[city] = payload
    return payloads


# ---------------------------------------------------------------------------
# 12. Daily Discovery Lists — most saved (7d), snapshot + cache
# ---------------------------------------------------------------------------
def compute_daily_discovery_lists():
    from app_ib.models import SavedItem, DailySnapshot
    cutoff = timezone.now() - timedelta(days=ALGO.DISCOVERY_WINDOW_DAYS)
    rows = (SavedItem.objects.filter(timestamp__gte=cutoff)
            .values("contentType_id", "objectId").annotate(c=Count("id")).order_by("-c"))
    items = [{"contentType": r["contentType_id"], "objectId": r["objectId"], "saveCount": r["c"]}
             for r in rows][:ALGO.DISCOVERY_TOP_N]
    today = timezone.now().date()
    DailySnapshot.objects.update_or_create(
        listKey="most_saved", snapshotDate=today, defaults={"payload": {"items": items}})
    cache.set("discovery:most_saved", items, ALGO.DISCOVERY_TTL_SECONDS)
    return items


def ensure_discovery_cache_warm():
    """Guardian: re-warm Redis from DailySnapshot WITHOUT re-aggregating.
    Returns the items (cached or from snapshot) so callers can serve them even
    when the cache backend is unavailable; None when nothing is available."""
    from app_ib.models import DailySnapshot
    cached = cache.get("discovery:most_saved")
    if cached is not None:
        return cached
    snap = DailySnapshot.objects.filter(listKey="most_saved").order_by("-snapshotDate").first()
    if snap:
        items = snap.payload.get("items", [])
        cache.set("discovery:most_saved", items, ALGO.DISCOVERY_TTL_SECONDS)
        return items
    return None
