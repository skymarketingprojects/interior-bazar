"""
EngineConfig.py — Centralized configuration + string constants for the v2.1.0.0
discovery/trending engine (ALGORITHMS_FINAL, MODEL_REVIEW_FINAL, INTEGRATION_FINAL).

Follows the zero-hardcoded-strings policy: every weight, window, period name,
event type and label string used by the new algorithms lives here, never inline
in logic. Algorithm code reads from these classes only.
"""


# ---------------------------------------------------------------------------
# Value constants (choice values / string identifiers)
# ---------------------------------------------------------------------------
class ENTITY_TYPE:
    BUSINESS = "business"
    SHOP = "shop"
    ARCHITECT = "architect"
    PRODUCT = "product"
    SERVICE = "service"
    CATELOGUE = "catelogue"
    # 'automation' is NOT a resolvable entity — it's a bundle plan family whose
    # purchase unlocks all three seller tabs (business/shop/architect). Kept out of
    # ALL/SCORED/RATED/COMPLETION so resolve/scoring never treat it as an entity.
    AUTOMATION = "automation"

    ALL = [BUSINESS, SHOP, ARCHITECT, PRODUCT, SERVICE, CATELOGUE]
    # entities that carry a trendingScore/hotScore field
    SCORED = [BUSINESS, SHOP, ARCHITECT, PRODUCT, SERVICE, CATELOGUE]
    # entities that get rating aggregation (Catelogue excluded per spec)
    RATED = [BUSINESS, SHOP, ARCHITECT, PRODUCT, SERVICE]
    # entities with a profile-completion checklist
    COMPLETION = [BUSINESS, SHOP, ARCHITECT]
    # seller-dashboard entity tabs a subscription can gate (buy-first model)
    GATED = [BUSINESS, SHOP, ARCHITECT]


class PLAN_STATUS:
    """Lifecycle of a purchased entity plan (BusinessPlan/ShopPlan/ArchitectPlan/
    AutomationPlan). Replaces the bare isActive bool — isActive is kept as a synced
    shim (isActive == (status == ACTIVE)) so legacy reads keep working."""
    PENDING = "pending"      # bought, awaiting verification/payment — tab visible, publish locked
    ACTIVE = "active"        # verified/paid — full access
    EXPIRED = "expired"      # lapsed past expireDate — must re-buy
    CANCELLED = "cancelled"  # withdrawn before activation
    REFUNDED = "refunded"    # money returned

    ALL = [PENDING, ACTIVE, EXPIRED, CANCELLED, REFUNDED]
    # statuses that still "hold" the plan → which entity TABS to show
    ENTITLED = [PENDING, ACTIVE]


class PLAN_FAMILY:
    """The frontend plan category (plans-checkout sidebar). 'automation' is the bundle
    that grants all three entity tabs; the other three are single-entity families."""
    AUTOMATION = "automation"
    BUSINESS = "business"
    SHOP = "shop"
    ARCHITECT = "architect"

    ALL = [AUTOMATION, BUSINESS, SHOP, ARCHITECT]


# Which entity tabs a plan unlocks, keyed by the plan's family/entityType. Automation
# is the only bundle (unlocks all three); every other family unlocks just its own tab.
# This is the single source of truth for "what does buying this plan grant" — the
# entitlement service reads it instead of branching on type in code.
PLAN_GRANTS = {
    PLAN_FAMILY.AUTOMATION: list(ENTITY_TYPE.GATED),
    PLAN_FAMILY.BUSINESS: [ENTITY_TYPE.BUSINESS],
    PLAN_FAMILY.SHOP: [ENTITY_TYPE.SHOP],
    PLAN_FAMILY.ARCHITECT: [ENTITY_TYPE.ARCHITECT],
}


class TRENDING_PERIOD:
    DAILY = "daily"
    WEEKLY = "weekly"
    ALL = [DAILY, WEEKLY]


class LEADERBOARD_PERIOD:
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ALL_TIME = "all_time"
    ALL = [WEEKLY, MONTHLY, ALL_TIME]


class LEADERBOARD_BOARD:
    COMBINED = "combined"
    PER_CATEGORY = "per_category"


class LEADERBOARD_SCOPE:
    CITY = "city"
    CATEGORY = "category"
    GLOBAL = "global"


class CLICK_TYPE:
    WHATSAPP = "whatsapp"
    CALL = "call"
    WEBSITE = "website"
    DIRECTIONS = "directions"
    EMAIL = "email"
    ALL = [WHATSAPP, CALL, WEBSITE, DIRECTIONS, EMAIL]
    # high-intent clicks counted in leaderboard score
    ENGAGEMENT = [WHATSAPP, CALL, WEBSITE]


class FEED_EVENT_TYPE:
    SAVE = "save"
    VIEW = "view"
    LEAD = "lead"
    REVIEW = "review"
    UPGRADE = "upgrade"      # business activated/upgraded a plan
    TRENDING = "trending"    # leaderboard / trending movement
    SYNTHETIC = "synthetic"


class ENGAGEMENT_VERB:
    """Inbound-engagement feed verbs (EngagementActivity) — what OTHER users did
    to a seller's own entities (business/shop/architect/product/service).

    WHY: powers the seller dashboard "Recent activity" feed ("someone viewed your
    product", "someone saved your shop", "someone filled your form"). Stored on
    EngagementActivity.verb (zero-hardcoded-strings) and mapped to a human action
    label via LABELS below.
    """
    VIEW = "view"
    SAVE = "save"
    ENQUIRY = "enquiry"      # a lead/form submission landed on the entity
    REVIEW = "review"
    WHATSAPP = "whatsapp"
    CALL = "call"
    WEBSITE = "website"
    ALL = [VIEW, SAVE, ENQUIRY, REVIEW, WHATSAPP, CALL, WEBSITE]

    # verb -> human action phrase shown in the feed ("{actor} {phrase}")
    LABELS = {
        VIEW: "viewed",
        SAVE: "saved",
        ENQUIRY: "filled a form on",
        REVIEW: "reviewed",
        WHATSAPP: "messaged on WhatsApp about",
        CALL: "called about",
        WEBSITE: "opened the website of",
    }

    # CLICK_TYPE -> engagement verb (only these click types become feed rows)
    FROM_CLICK = {"whatsapp": WHATSAPP, "call": CALL, "website": WEBSITE}

    # Display name used when the actor is anonymous (unauthenticated).
    ANON_ACTOR = "Someone"

    # Dedupe window (minutes): a repeat (owner, actor, entity, verb) within this
    # window bumps the existing row's count/timestamp instead of inserting a new
    # one — keeps high-frequency views from flooding the feed.
    DEDUPE_MINUTES = 360


class CONVERSATION_STATUS:
    REQUESTED = "requested"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    CLOSED = "closed"
    ALL = [REQUESTED, ACCEPTED, DECLINED, CLOSED]


class NOTIFICATION_TYPE:
    LEAD = "lead"
    PAYMENT = "payment"
    PLAN = "plan"
    REVIEW = "review"
    SYSTEM = "system"
    PROMO = "promo"
    CHAT = "chat"


class TEAM_ROLE:
    OWNER = "owner"
    MANAGER = "manager"
    STAFF = "staff"
    VIEWER = "viewer"


class SHOP_TYPE:
    OFFLINE = "offline"
    ONLINE = "online"
    HYBRID = "hybrid"


class DISCOUNT_TYPE:
    FLAT = "flat"
    PERCENT = "percent"


class LABEL:
    TRENDING = "Trending"
    BESTSELLER = "Bestseller"
    NEW = "New"
    NONE = ""
    # priority order: Trending > Bestseller > New
    PRIORITY = [TRENDING, BESTSELLER, NEW]


class PLAN_TIER:
    PREMIUM = "premium"
    PRO = "pro"
    BASIC = "basic"
    FREE = "free"


class TRENDING_SCORE_PERIOD:
    DAILY = "daily"
    WEEKLY = "weekly"


class HOME_FILTER:
    """Home-page filter-bar vocabulary (GET home/filters/ + home/for-you/ params).

    WHY: the filter bar is data-driven — the frontend renders whatever this
    endpoint returns, so codes/labels/icons live here (zero-hardcoded-strings)
    and stay in sync between the /home/filters/ payload and the for-you
    query-param handling.
    """
    # item kinds
    KIND_BASIC = "basic"        # fixed filters every marketplace has
    KIND_CATEGORY = "category"  # derived from the user's recently-viewed items
    # basic filter codes (the value the frontend sends back as ?filter=<code>)
    NEAR_ME = "near_me"
    OPEN_NOW = "open_now"
    VERIFIED = "verified"
    TOP_RATED = "top_rated"
    CODES = [NEAR_ME, OPEN_NOW, VERIFIED, TOP_RATED]
    # (code, label, icon) — icon names are tabler-icon ids, matching the
    # frontend's existing static pills so visuals don't change.
    BASIC = [
        (NEAR_ME, "Near me", "map-pin"),
        (OPEN_NOW, "Open now", "clock"),
        (VERIFIED, "Verified", "rosette"),
        (TOP_RATED, "Top rated", "star"),
    ]
    TOP_RATED_MIN = 4.0          # ratingValue floor for the top_rated filter
    MAX_CATEGORY_PILLS = 8       # cap on derived/fallback category pills
    RECENT_ROWS = 10             # how many RecentlyViewed rows feed the derivation
    # Radius (km) the for-you feed restricts to once ANY filter/category is
    # active and the user's lat/lng are known. Deliberately wider than the
    # 10km nearby_search() cap (ALGO.NEARBY_MAX_RADIUS_KM): the home feed wants
    # "businesses in my area/city", not "walking distance". Overridable per
    # request via ?radiusKm=. We reuse haversine_km() directly (not
    # nearby_search(), which hard-caps at 10km) to honour this larger radius.
    FORYOU_RADIUS_KM = 100.0
    RECENT_VIEW_CATEGORY_BOOST = 4.0  # score bump per shared category w/ recently-viewed items
    POPULAR_CACHE_KEY = "home:filters:popular_categories"
    POPULAR_CACHE_TTL = 60 * 60  # 1h — taxonomy changes rarely


# ---------------------------------------------------------------------------
# Algorithm configuration blocks (weights / windows / thresholds)
# ---------------------------------------------------------------------------
class ALGO:
    # --- 1. Trending Score ---
    # weight maps keyed by signal, per period
    TRENDING_WEIGHTS = {
        TRENDING_PERIOD.DAILY: {
            "view": 1.0, "click": 2.0, "save": 3.0, "lead": 8.0, "download": 3.0,
        },
        TRENDING_PERIOD.WEEKLY: {
            "view": 0.5, "click": 1.5, "save": 2.0, "lead": 5.0, "download": 2.0,
        },
    }
    TRENDING_DECAY_LAMBDA = 0.02            # half-life ~= 35 hours
    TRENDING_WINDOW_HOURS = {TRENDING_PERIOD.DAILY: 24, TRENDING_PERIOD.WEEKLY: 24 * 7}

    # --- 2. Hot Score ---  hot = views_1h*10 + views_6h*3 + leads_24h*20
    HOT_WEIGHTS = {"views_1h": 10.0, "views_6h": 3.0, "leads_24h": 20.0}

    # --- 3. Leaderboard ---  score = genuineViews*1 + clicks*5
    LEADERBOARD_WEIGHTS = {"genuine_views": 1.0, "clicks": 5.0}
    LEADERBOARD_PERSIST_TOP = 100
    LEADERBOARD_CACHE_TOP = 20
    LEADERBOARD_PERIOD_DAYS = {
        LEADERBOARD_PERIOD.WEEKLY: 7,
        LEADERBOARD_PERIOD.MONTHLY: 30,
        LEADERBOARD_PERIOD.ALL_TIME: None,   # no window
    }

    # --- 4. Behind the Trend ---
    BEHIND_TREND_WEIGHTS = {"leaderboard": 0.6, "trending": 0.4}
    BEHIND_TREND_PLAN_MULTIPLIER = {
        PLAN_TIER.PREMIUM: 1.6, PLAN_TIER.PRO: 1.3, PLAN_TIER.BASIC: 1.1, PLAN_TIER.FREE: 1.0,
    }
    BEHIND_TREND_TOP_N = 5
    BEHIND_TREND_GEMINI_TEMPERATURE = 0.8

    # --- 5. Profile Completion ---  max recalcs/day
    COMPLETION_MAX_PER_DAY = 4

    # --- 6. Nearby Haversine ---
    EARTH_RADIUS_KM = 6371.0
    NEARBY_DEFAULT_RADIUS_KM = 10.0
    NEARBY_MAX_RADIUS_KM = 10.0

    # --- 7. Search Ranking ---
    SEARCH_TEXT_WEIGHT = 2.0
    SEARCH_SUBSCRIPTION_MULTIPLIER = 1.5
    SEARCH_TRENDING_WEIGHT = 0.01
    SEARCH_RATING_WEIGHT = 0.3

    # --- 8. Lead Prioritization ---
    LEAD_PRIORITY_WEIGHTS = {
        "recency": 32.0,
        "message_count": 15.0,
        "unanswered": 25.0,
        "high_value_tag": 10.0,
        "contact_eligible": 5.0,
        "source_channel": 8.0,
    }
    LEAD_PRIORITY_RECENCY_HALFLIFE_HOURS = 36.0
    LEAD_PRIORITY_HIGH_VALUE_TAGS = []      # starts empty per spec
    LEAD_PRIORITY_SOURCE_WEIGHTS = {}       # channel -> weight; empty default
    LEAD_PRIORITY_TOP_N = 50
    LEAD_OPEN_STATUSES = ["pending", "accepted", "in_progress", "lead", "contacted", "followed_up"]

    # --- 9. City Pulse ---
    CITY_PULSE_TOP_BUSINESSES = 10
    CITY_PULSE_TOP_SEARCHES = 10
    CITY_PULSE_TTL_SECONDS = 2 * 60 * 60

    # --- 10. Trending Searches ---
    TRENDING_SEARCH_WINDOW_HOURS = 24
    TRENDING_SEARCH_MIN_COUNT = 5
    TRENDING_SEARCH_TOP_N = 20
    SEARCH_COUNT_DEDUPE_MINUTES = 5
    TRENDING_SEARCH_TTL_SECONDS = 60 * 60

    # --- 12. Daily Discovery ---
    DISCOVERY_WINDOW_DAYS = 7
    DISCOVERY_TOP_N = 20
    DISCOVERY_TTL_SECONDS = 24 * 60 * 60

    # --- 18. Synthetic Feed ---
    SYNTHETIC_MIN_REAL_EVENTS = 8
    SYNTHETIC_REAL_WINDOW_MINUTES = 5
    SYNTHETIC_MAX_BLEND_PCT = 0.70

    # --- 19. Genuine View Dedup ---
    GENUINE_VIEW_DEDUP_WINDOW_HOURS = 24
    GENUINE_VIEW_MIN_DWELL_SECONDS = 2

    # --- 20. Notification Dedupe ---
    NOTIFICATION_DEDUPE_WINDOW_SECONDS = 60 * 60

    # --- 21. Recently Viewed ---
    RECENTLY_VIEWED_CAP = 50

    # --- 22. Average Response Time ---
    AVG_RESPONSE_WINDOW_DAYS = 30

    # --- retention ---
    VIEW_EVENT_RETENTION_DAYS = 90
    SEARCH_EVENT_RETENTION_DAYS = 90
    ACCOUNT_DELETION_GRACE_DAYS = 30

    # --- AI Specialization ("what they specialize in" cards) ---
    # Bootstrap = a one-time debounced job that creates the FIRST specialization.
    # After bootstrap, regeneration is gated by SPEC_CHANGE_THRESHOLD via the drift cron.
    SPEC_DEBOUNCE_SECONDS = 3600          # one-time bootstrap debounce window (1 hr)
    SPEC_CHANGE_THRESHOLD = 0.25          # profile-text drift (0-1) needed to regenerate
    SPEC_CARD_CAP = 6                     # max specialization cards
    SPEC_GEMINI_TEMPERATURE = 0.5
    SPEC_GEMINI_MAX_TOKENS = 600
    SPEC_ICONS = [                        # allowed Tabler icon names for cards
        "building", "palette", "tools", "home", "armchair",
        "ruler", "map-pin", "calendar-stats", "bulb", "brush",
    ]


# ---------------------------------------------------------------------------
# Profile-completion checklists (key, label, weight, isLiveGate)
# ---------------------------------------------------------------------------
class COMPLETION_CHECKLIST:
    BUSINESS = [
        {"key": "subscription", "label": "Active subscription", "weight": 30, "isLiveGate": True},
        {"key": "business_name", "label": "Business name", "weight": 15, "isLiveGate": False},
        {"key": "bio", "label": "Bio / description", "weight": 15, "isLiveGate": False},
        {"key": "cover_image", "label": "Cover image", "weight": 15, "isLiveGate": False},
        {"key": "category", "label": "Category set", "weight": 10, "isLiveGate": False},
        {"key": "contact_info", "label": "Contact info", "weight": 8, "isLiveGate": False},
        {"key": "location", "label": "Location / city", "weight": 7, "isLiveGate": False},
    ]
    ARCHITECT = [
        {"key": "subscription", "label": "Active subscription", "weight": 30, "isLiveGate": True},
        {"key": "portfolio", "label": "Portfolio items", "weight": 30, "isLiveGate": True},
        {"key": "bio", "label": "Bio / description", "weight": 18, "isLiveGate": False},
        {"key": "cover_image", "label": "Cover image", "weight": 14, "isLiveGate": False},
        {"key": "city_state", "label": "City / state", "weight": 8, "isLiveGate": False},
    ]
    SHOP = [
        {"key": "subscription", "label": "Active subscription", "weight": 25, "isLiveGate": True},
        {"key": "location", "label": "Location set", "weight": 20, "isLiveGate": True},
        {"key": "contact_info", "label": "Contact info", "weight": 20, "isLiveGate": True},
        {"key": "cover_image", "label": "Cover image", "weight": 15, "isLiveGate": False},
        {"key": "hours", "label": "Working hours", "weight": 12, "isLiveGate": False},
        {"key": "bio", "label": "Bio", "weight": 8, "isLiveGate": False},
    ]

    BY_ENTITY = {
        ENTITY_TYPE.BUSINESS: BUSINESS,
        ENTITY_TYPE.ARCHITECT: ARCHITECT,
        ENTITY_TYPE.SHOP: SHOP,
    }
