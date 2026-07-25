"""Request-time ranking algorithms:
  6. Nearby Haversine     nearby_search()
  7. Search Ranking       search_rank()
  8. Lead Prioritization  prioritize_leads()
"""
import math
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q

from app_ib.Utils.EngineConfig import ENTITY_TYPE, ALGO
from app_ib.algorithms.helpers import get_model, haversine_km
from app_ib.algorithms.text import normalize


# ---------------------------------------------------------------------------
# 6. Nearby Haversine — sort by distance asc within radius (hard cap 10 km)
# ---------------------------------------------------------------------------
def nearby_search(user_lat, user_lng, coords, radius_km=None):
    """coords: iterable of (entity_id, lat, lng). Returns [(entity_id, distance_km)]."""
    radius = min(radius_km or ALGO.NEARBY_DEFAULT_RADIUS_KM, ALGO.NEARBY_MAX_RADIUS_KM)
    out = []
    for eid, lat, lng in coords:
        if lat is None or lng is None:
            continue
        d = haversine_km(user_lat, user_lng, float(lat), float(lng))
        if d <= radius:
            out.append((eid, round(d, 3)))
    out.sort(key=lambda t: t[1])
    return out


# ---------------------------------------------------------------------------
# 7. Search Ranking — text*subMult*2 + trending*0.01 + rating*0.3
# ---------------------------------------------------------------------------
def search_rank(entity_type, query, subscribed_ids=None, limit=50):
    model = get_model(entity_type)
    nq = normalize(query)
    subscribed_ids = subscribed_ids or set()

    name_field = {
        ENTITY_TYPE.BUSINESS: "businessName",
        ENTITY_TYPE.SHOP: "name", ENTITY_TYPE.ARCHITECT: "name",
    }.get(entity_type, "title")

    text_filter = Q(**{f"{name_field}__icontains": nq})
    if entity_type == ENTITY_TYPE.BUSINESS:
        text_filter |= Q(bio__icontains=nq)
    elif entity_type in (ENTITY_TYPE.PRODUCT, ENTITY_TYPE.SERVICE):
        text_filter |= Q(description__icontains=nq)

    results = []
    for obj in model.objects.filter(text_filter):
        name = getattr(obj, name_field, "") or ""
        # crude text match score: 1.0 exact-substring on name, 0.6 elsewhere
        text_match = 1.0 if nq and nq in name.lower() else 0.6
        sub_mult = ALGO.SEARCH_SUBSCRIPTION_MULTIPLIER if obj.id in subscribed_ids else 1.0
        rating = getattr(obj, "ratingValue", 0.0) or 0.0
        trending = getattr(obj, "trendingScore", 0.0) or 0.0
        score = (text_match * sub_mult * ALGO.SEARCH_TEXT_WEIGHT
                 + trending * ALGO.SEARCH_TRENDING_WEIGHT
                 + rating * ALGO.SEARCH_RATING_WEIGHT)
        results.append({"id": obj.id, "name": name, "score": round(score, 4)})
    results.sort(key=lambda d: d["score"], reverse=True)
    return results[:limit]


# ---------------------------------------------------------------------------
# 8. Lead Prioritization — top 50 with factor breakdown + "why"
# ---------------------------------------------------------------------------
def prioritize_leads(business):
    from app_ib.models import LeadQuery
    now = timezone.now()
    w = ALGO.LEAD_PRIORITY_WEIGHTS
    halflife = ALGO.LEAD_PRIORITY_RECENCY_HALFLIFE_HOURS
    high_value = set(ALGO.LEAD_PRIORITY_HIGH_VALUE_TAGS)
    source_weights = ALGO.LEAD_PRIORITY_SOURCE_WEIGHTS

    leads = LeadQuery.objects.filter(business=business)
    if ALGO.LEAD_OPEN_STATUSES:
        leads = leads.filter(Q(leadStatus__in=ALGO.LEAD_OPEN_STATUSES) |
                             Q(status__in=ALGO.LEAD_OPEN_STATUSES) | Q(leadStatus="") | Q(status=""))

    scored = []
    for lead in leads:
        factors = {}
        # recency: exponential decay over 36h half-life
        age_h = max(0.0, (now - lead.timestamp).total_seconds() / 3600.0)
        recency = w["recency"] * math.pow(0.5, age_h / halflife)
        factors["recency"] = round(recency, 2)
        # message count
        mc = getattr(lead, "messageCount", 0) or 0
        factors["message_count"] = round(min(w["message_count"], mc * 3.0), 2)
        # unanswered (no business response yet)
        factors["unanswered"] = w["unanswered"] if lead.respondedAt is None else 0.0
        # high-value tag
        factors["high_value_tag"] = w["high_value_tag"] if (lead.tag or "") in high_value else 0.0
        # contact eligibility
        factors["contact_eligible"] = w["contact_eligible"] if (lead.phone or lead.email) else 0.0
        # source channel
        factors["source_channel"] = round(source_weights.get(lead.sourceChannel or "", 0.0), 2)

        total = round(sum(factors.values()), 2)
        scored.append({
            "lead_id": lead.id, "score": total, "factors": factors,
            "why": _why(factors, lead),
        })
    scored.sort(key=lambda d: d["score"], reverse=True)
    return scored[:ALGO.LEAD_PRIORITY_TOP_N]


def _why(factors, lead):
    bits = []
    if factors["recency"] > factors_threshold(factors, "recency"):
        bits.append("fresh connection")
    if factors["unanswered"]:
        bits.append("unanswered")
    if factors["high_value_tag"]:
        bits.append("high-value tagged customer")
    if factors["contact_eligible"]:
        bits.append("contact details present")
    return ", ".join(bits).capitalize() if bits else "Open lead"


def factors_threshold(factors, key):
    return ALGO.LEAD_PRIORITY_WEIGHTS[key] * 0.5
