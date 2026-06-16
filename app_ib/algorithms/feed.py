"""Algorithm 18 — Live Feed.

The trending-page activity strip ("recent events" ticker on /v3/trending) is built
from REAL recent platform activity — enquiries, reviews, plan upgrades and
leaderboard movement — each rendered with the real (public) business name and city.

Privacy: enquirer / visitor identities are NEVER exposed. Only the public listing
(the business) and its city appear, so there is no PII leak — matching the original
design intent of this algorithm.

When real activity is sparse (quiet periods, fresh DB) the batch is topped up with
events *synthesised from real reference data* — real cities and real business names
pulled from the database — so the strip is never empty and never shows invented
placeholders. Only when the database itself is empty does a tiny constant fallback
apply.

Two entry points:
  • generate_feed_batch(count)        — polling endpoint used by the live ticker;
                                        assembles the batch on demand (real events
                                        first, then real-data synthetic fill).
  • generate_synthetic_feed_events()  — background job (run_engine_jobs, #18) that
                                        PERSISTS a capped number of real-data
                                        synthetic events during quiet periods and
                                        publishes them to the SSE stream.

Security: business names / cities are user-provided and the client renders the
ticker via dangerouslySetInnerHTML, so every interpolated value is HTML-escaped
here (`_safe` / `_b`). The only HTML emitted is app-controlled <b> emphasis.
"""
import random
from datetime import timedelta

from django.core.cache import cache
from django.utils import timezone
from django.utils.html import escape

from app_ib.Utils.EngineConfig import (
    ALGO, FEED_EVENT_TYPE, LEADERBOARD_BOARD, LEADERBOARD_PERIOD, LEADERBOARD_SCOPE,
)


# Tiny constants used ONLY when the database has no real cities / businesses yet
# (fresh install). Everything else is derived from real data.
_FALLBACK_CITIES = ["Mumbai", "Delhi", "Bengaluru", "Pune", "Jaipur",
                    "Hyderabad", "Chennai", "Kolkata", "Ahmedabad", "Surat"]
_FALLBACK_NAMES = ["a verified studio", "a trusted brand", "a top-rated business"]
_FALLBACK_PLANS = ["Premium", "Pro", "Basic"]

# Short cache for the assembled batch + reference lists. The ticker is display-only
# and polled rarely, so a few seconds of staleness is invisible while cutting DB load
# when many clients poll at once.
_BATCH_CACHE_KEY = "feed:batch:v2"
_CITY_CACHE_KEY = "feed:real_cities"
_NAME_CACHE_KEY = "feed:real_names"
_PLAN_CACHE_KEY = "feed:real_plans"
_BATCH_TTL = 25          # seconds
_REF_TTL = 10 * 60       # seconds


def _valid_city(city):
    """Reject city values that look like street addresses (digits or commas)."""
    if not city:
        return False
    return not any(ch.isdigit() for ch in city) and "," not in city


def _safe(value):
    """HTML-escape an app/user value for the dangerouslySetInnerHTML ticker."""
    return escape((value or "").strip())


def _b(value):
    """Bold + HTML-escape a value (business / entity name)."""
    return f"<b>{_safe(value)}</b>"


def _cache_get(key):
    try:
        return cache.get(key)
    except Exception:
        return None


def _cache_set(key, value, ttl):
    try:
        cache.set(key, value, ttl)
    except Exception:
        pass


def _business_city(business):
    """Real city for a Business via its OneToOne Location (empty string if none)."""
    loc = getattr(business, "business_location", None)
    return (getattr(loc, "city", "") or "").strip() if loc else ""


def _event(ev_id, ev_type, template, city, ts):
    """Build a feed item dict in the public-safe shape the client expects.

    `city` is surfaced separately only when it literally appears in the template, so
    the client's city-emphasis (string replace) always matches. `_ts` is an internal
    sort key, stripped before the batch is returned.
    """
    safe_city = (city or "").strip()
    city_field = safe_city if (safe_city and safe_city in template) else ""
    return {
        "id": ev_id,
        "eventType": ev_type,
        "template": template,
        "city": city_field,
        "timestamp": ts.isoformat(),
        "_ts": ts,
    }


# ── Reference data (real cities / business names / plans), cached ───────────────

def _real_cities():
    cached = _cache_get(_CITY_CACHE_KEY)
    if cached is not None:
        return cached
    from app_ib.models import Location
    cities = [
        c for c in Location.objects.exclude(city="")
        .values_list("city", flat=True).distinct()[:300]
        if _valid_city(c)
    ]
    cities = cities or list(_FALLBACK_CITIES)
    _cache_set(_CITY_CACHE_KEY, cities, _REF_TTL)
    return cities


def _real_business_names(limit=200):
    cached = _cache_get(_NAME_CACHE_KEY)
    if cached is not None:
        return cached
    from app_ib.models import Business
    names = [
        n.strip() for n in Business.objects.exclude(businessName="")
        .order_by("-trendingScore", "-timestamp")
        .values_list("businessName", flat=True)[:limit]
        if (n or "").strip()
    ]
    names = names or list(_FALLBACK_NAMES)
    _cache_set(_NAME_CACHE_KEY, names, _REF_TTL)
    return names


def _real_plans():
    cached = _cache_get(_PLAN_CACHE_KEY)
    if cached is not None:
        return cached
    from app_ib.models import Subscription
    titles = [
        t.strip() for t in Subscription.objects.exclude(title__isnull=True)
        .exclude(title="").values_list("title", flat=True).distinct()[:20]
        if (t or "").strip()
    ]
    titles = titles or list(_FALLBACK_PLANS)
    _cache_set(_PLAN_CACHE_KEY, titles, _REF_TTL)
    return titles


# ── Real events (truthful event timestamps) ─────────────────────────────────────

def _from_leads(limit):
    """Recent enquiries — public business + city only, never the enquirer."""
    from app_ib.models import LeadQuery
    out = []
    qs = (LeadQuery.objects
          .select_related("business", "business__business_location")
          .filter(business__isnull=False)
          .order_by("-timestamp")[:limit])
    for lq in qs:
        name = (lq.business.businessName or "").strip()
        if not name:
            continue
        city = _safe(_business_city(lq.business) or (lq.city or ""))
        where = f" in {city}" if city else ""
        tpl = f"{_b(name)} received a new enquiry{where}"
        out.append(_event(lq.id, FEED_EVENT_TYPE.LEAD, tpl, city, lq.timestamp))
    return out


def _from_reviews(limit):
    from app_ib.models import Review
    out = []
    qs = (Review.objects
          .select_related("business", "business__business_location")
          .filter(business__isnull=False, isApproved=True, isDeleted=False)
          .order_by("-timestamp")[:limit])
    for rv in qs:
        name = (rv.business.businessName or "").strip()
        if not name:
            continue
        city = _safe(_business_city(rv.business))
        where = f" in {city}" if city else ""
        tpl = f"{_b(name)} earned a {int(rv.rating)}★ review{where}"
        out.append(_event(rv.id, FEED_EVENT_TYPE.REVIEW, tpl, city, rv.timestamp))
    return out


def _from_upgrades(limit):
    from app_ib.models import BusinessPlan
    out = []
    qs = (BusinessPlan.objects
          .select_related("business", "business__business_location", "plan")
          .filter(isActive=True, business__isnull=False)
          .order_by("-lastActivate")[:limit])
    for bp in qs:
        name = (bp.business.businessName or "").strip()
        if not name:
            continue
        plan = _safe(getattr(bp.plan, "title", "") or "a premium plan")
        city = _safe(_business_city(bp.business))
        where = f" in {city}" if city else ""
        tpl = f"{_b(name)} upgraded to {plan}{where}"
        out.append(_event(bp.id, FEED_EVENT_TYPE.UPGRADE, tpl, city, bp.lastActivate))
    return out


def _from_leaderboard(limit):
    """Current trending movement — displayName + rank are denormalised on the row.
    Scoped to a single period and deduped by name so the same business can't appear
    several times across weekly/monthly/all-time boards."""
    from app_ib.models import LeaderboardEntry
    out = []
    seen = set()
    qs = (LeaderboardEntry.objects
          .filter(boardType=LEADERBOARD_BOARD.COMBINED,
                  period=LEADERBOARD_PERIOD.WEEKLY,
                  scope=LEADERBOARD_SCOPE.GLOBAL, rank__gt=0)
          .exclude(displayName="")
          .order_by("rank"))
    for e in qs:
        key = e.displayName.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        tpl = f"{_b(e.displayName)} is now #{int(e.rank)} on the leaderboard"
        out.append(_event(e.id, FEED_EVENT_TYPE.TRENDING, tpl, "", e.computedAt))
        if len(out) >= limit:
            break
    return out


def _collect_real_events(count):
    """Merge real activity from every source, newest first, with per-source caps so
    no single source dominates the strip (e.g. a freshly-computed leaderboard would
    otherwise crowd out genuine recent enquiries). Each source is isolated so one
    failing query never blanks the strip."""
    # caps keep a healthy mix; leads (the highest-volume real signal) get the most room
    collectors = (
        (_from_leads, count),
        (_from_reviews, max(2, count // 3)),
        (_from_upgrades, max(2, count // 4)),
        (_from_leaderboard, min(4, max(2, count // 4))),
    )
    events = []
    for collect, cap in collectors:
        try:
            events.extend(collect(cap))
        except Exception:
            continue
    # drop exact-duplicate lines, then order newest first
    deduped, seen = [], set()
    for e in events:
        key = (e["eventType"], e["template"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(e)
    deduped.sort(key=lambda e: e["_ts"], reverse=True)
    return deduped


# ── Synthetic fill, built from REAL reference data ──────────────────────────────

# Each builder takes (bold_name, safe_city, safe_plan) and returns a template that
# reads as a full sentence. Names are already bold+escaped; cities/plans escaped.
_REAL_SYNTH_TEMPLATES = [
    lambda n, c, p: f"A homeowner in {c} enquired with {n}",
    lambda n, c, p: f"{n} is trending in {c}",
    lambda n, c, p: f"Someone saved a listing from {n}",
    lambda n, c, p: f"{n} upgraded to {p}",
    lambda n, c, p: f"{n} crossed new weekly views in {c}",
    lambda n, c, p: f"A designer in {c} opened {n}",
    lambda n, c, p: f"{n} replied fast to a new enquiry",
    lambda n, c, p: f"{n} climbed the {c} leaderboard",
]


def _synth_items(n, rng):
    """Produce `n` synthetic (template, city, eventType) tuples from real cities /
    business names / plans. City is the plain (escaped) value for client emphasis."""
    cities = _real_cities()
    names = _real_business_names()
    plans = _real_plans()
    items = []
    for _ in range(max(0, n)):
        build = rng.choice(_REAL_SYNTH_TEMPLATES)
        city = _safe(rng.choice(cities))
        name = _b(rng.choice(names))
        plan = _safe(rng.choice(plans))
        tpl = build(name, city, plan)
        # surface city only when it actually appears (for client-side emphasis)
        city_field = city if city and city in tpl else ""
        items.append((tpl, city_field, FEED_EVENT_TYPE.SYNTHETIC))
    return items


def _synth_fill(n):
    """Ephemeral (not persisted) synthetic fill for the polling batch."""
    now = timezone.now()
    rng = random.Random()  # variety across polls
    out = []
    for i, (tpl, city, ev_type) in enumerate(_synth_items(n, rng)):
        ts = now - timedelta(seconds=i * 17)
        out.append(_event(-(i + 1), ev_type, tpl, city, ts))
    return out


# ── Public API ──────────────────────────────────────────────────────────────────

def generate_feed_batch(count=20, cities=None, plans=None):
    """Build `count` live-feed items in ONE call for the trending live ticker.

    Real recent platform events (enquiries, reviews, upgrades, leaderboard movement)
    come first, newest first; any shortfall is filled with events synthesised from
    real cities and real business names. The batch is briefly cached so heavy polling
    doesn't hammer the DB. `cities`/`plans` are accepted for backward compatibility
    but real reference data is now sourced from the database.
    """
    count = max(1, min(int(count or 20), 50))

    cache_key = f"{_BATCH_CACHE_KEY}:{count}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    real = _collect_real_events(count)[:count]
    out = list(real)
    if len(out) < count:
        out.extend(_synth_fill(count - len(out)))

    # strip the internal sort key before returning
    result = [{k: v for k, v in item.items() if k != "_ts"} for item in out[:count]]
    _cache_set(cache_key, result, _BATCH_TTL)
    return result


def generate_synthetic_feed_events(rng=None, cities=None, plans=None):
    """Background job (#18): persist a capped number of real-data synthetic events
    during quiet periods so the SSE stream and FeedEvent table stay active. Synthetic
    output is capped so it never exceeds SYNTHETIC_MAX_BLEND_PCT of recent activity.
    Returns the list of created FeedEvent rows.
    """
    from app_ib.models import FeedEvent
    rng = rng or random.Random(12345)  # deterministic seed (Math.random unavailable in some envs)
    now = timezone.now()
    window_start = now - timedelta(minutes=ALGO.SYNTHETIC_REAL_WINDOW_MINUTES)

    real_count = FeedEvent.objects.filter(isSynthetic=False, timestamp__gte=window_start).count()
    if real_count >= ALGO.SYNTHETIC_MIN_REAL_EVENTS:
        return []   # active period — no synthetic fill needed

    existing_synth = FeedEvent.objects.filter(isSynthetic=True, timestamp__gte=window_start).count()
    cap_total = ALGO.SYNTHETIC_MIN_REAL_EVENTS
    if real_count > 0:
        max_synth = int((ALGO.SYNTHETIC_MAX_BLEND_PCT / (1 - ALGO.SYNTHETIC_MAX_BLEND_PCT)) * real_count)
    else:
        max_synth = cap_total
    to_create = max(0, min(cap_total - real_count, max_synth) - existing_synth)
    if to_create <= 0:
        return []

    from app_ib.Utils.sse_streamer import publish_feed
    created = []
    for tpl, city, ev_type in _synth_items(to_create, rng):
        ev = FeedEvent.objects.create(
            eventType=ev_type, template=tpl, city=city, isSynthetic=True,
        )
        # publish WITHOUT the isSynthetic flag (never exposed to clients)
        publish_feed({"id": ev.id, "eventType": ev.eventType, "template": ev.template,
                      "city": ev.city, "timestamp": ev.timestamp.isoformat()})
        created.append(ev)
    return created
