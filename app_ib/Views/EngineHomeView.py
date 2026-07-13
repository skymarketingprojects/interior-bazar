"""Home-page section views (sync DRF). Mostly public; 'for you' personalizes when
a JWT is present but still works anonymously (city-only).

Canonical responder stack (task 20): @exceptionHandler(responseFunc=ServerResponse,
errorMessage=...) wraps each view; views return ServerResponse(...) directly."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.decorators.ViewDecorator import exceptionHandler
from app_ib.Utils.EngineConfig import ENTITY_TYPE, HOME_FILTER
from app_ib.Controllers.Engine.HomeController import HOME_CONTROLLER


def _user(request):
    u = getattr(request, "user", None)
    return u if (u and u.is_authenticated) else None


# filler words stripped from a "?near=" search phrase ("near me jaipur" -> "jaipur")
_NEAR_STOP = {"near", "me", "in", "around", "my", "the", "at", "nearby", "close", "to"}


def _resolve_location(request):
    """Resolve (city, state) for the home sections so a section can always be
    location-relevant AND never empty:

      1. signed-in user with a saved address  -> use it;
      2. else query params the frontend sets from referrer/search context when
         geolocation is denied: ?city= / ?state= / ?near=  (?near= is a free-text
         "near me <city>" phrase, so filler words are stripped);
      3. else ("" , "") -> controllers broaden to all data.

    Never raises; a missing/partial address just yields "" for that field."""
    u = _user(request)
    if u is not None:
        try:
            loc = getattr(u, "user_location", None)
            if loc is not None:
                state = loc.locationState.name if loc.locationState else ""
                if loc.city or state:
                    return (loc.city or "", state)
        except Exception:
            pass
    p = request.GET
    city = (p.get("city") or "").strip()
    state = (p.get("state") or "").strip()
    if not city and p.get("near"):
        tokens = [t for t in p["near"].split() if t.lower() not in _NEAR_STOP]
        city = " ".join(tokens).strip()
    return (city, state)


# 1. Trending reels
@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ReelsView(request):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=HOME_CONTROLLER.reels())


# 2/3/4/7. For-you recommendations (business/product/service/catelogue)
# Optional params (all additive — omit them and the response is unchanged):
#   filter=near_me|open_now|verified|top_rated  (basic pill from home/filters/)
#   categoryId=<BusinessCategory id>            (category pill from home/filters/)
#   lat/lng  — when a filter/category is active these enable the ~100km radius
#              (haversine) restriction; with no filter they're inert (no geo).
#   radiusKm — override the default for-you radius (HOME_FILTER.FORYOU_RADIUS_KM).
@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ForYouView(request, entityType):
    if entityType not in (ENTITY_TYPE.BUSINESS, ENTITY_TYPE.PRODUCT,
                          ENTITY_TYPE.SERVICE, ENTITY_TYPE.CATELOGUE):
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request,
                              message=RESPONSE_MESSAGES.unsupported_entity_type, data={})
    # unknown filter codes / malformed ids are ignored, never an error — a stale
    # frontend pill must degrade to the unfiltered feed, not break the home page
    filter_code = request.GET.get("filter", "")
    if filter_code not in HOME_FILTER.CODES:
        filter_code = ""
    try:
        category_id = int(request.GET.get("categoryId", "") or 0) or None
    except (TypeError, ValueError):
        category_id = None
    try:
        lat = float(request.GET["lat"]) if request.GET.get("lat") else None
        lng = float(request.GET["lng"]) if request.GET.get("lng") else None
    except (TypeError, ValueError):
        lat = lng = None
    try:
        radius_km = float(request.GET["radiusKm"]) if request.GET.get("radiusKm") else None
    except (TypeError, ValueError):
        radius_km = None
    city, state = _resolve_location(request)
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=HOME_CONTROLLER.recommend(entityType, user=_user(request),
                                                         city=city, state=state,
                                                         filter_code=filter_code,
                                                         category_id=category_id,
                                                         lat=lat, lng=lng, radius_km=radius_km))


# 0. Home filter bar — basic pills (with icons) + personalized category pills.
# AllowAny: anonymous users get the platform-popular categories; a valid JWT
# (resolved by _user, same pattern as ForYouView) personalizes from history.
@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def HomeFiltersView(request):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=HOME_CONTROLLER.home_filters(user=_user(request)))


# 5. Verified business = architects (legacy; kept for the architects page)
@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ArchitectsRecommendedView(request):
    city, state = _resolve_location(request)
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=HOME_CONTROLLER.recommend_architects(user=_user(request),
                                                                    city=city, state=state))


# 5b. Verified businesses — ranked by the combined verified-business score
# (proximity + relative age + completed 'won' leads + conversion + response time
# + rating). Powers the home "Verified businesses" section.
@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def VerifiedBusinessesView(request):
    city, state = _resolve_location(request)
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=HOME_CONTROLLER.verified_businesses(user=_user(request),
                                                                   city=city, state=state))


# "Join us" — final CTA band (eyebrow/heading/desc/buttons/trust-tags/process steps).
@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def JoinUsView(request):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=HOME_CONTROLLER.join_us())


# "What makes IB different" — differentiator cards (icon/heading/description/eliminates).
@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def DifferentiatorsView(request):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=HOME_CONTROLLER.differentiators())


# 8. Get inspired — most-popular products/services as a photo gallery.
@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def GetInspiredView(request):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=HOME_CONTROLLER.get_inspired())


# 7b. Fresh catalogues — "Fresh from manufacturers": newest catalogues, daily cron.
@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def FreshCataloguesView(request):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=HOME_CONTROLLER.fresh_catalogues())


# 6. Shops near you
@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ShopsNearbyView(request):
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    radius = request.GET.get("radius")
    city, state = _resolve_location(request)
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=HOME_CONTROLLER.nearby_shops(
                              float(lat) if lat else None, float(lng) if lng else None,
                              float(radius) if radius else None, city=city, state=state))


# 9. Video stories = testimonials
@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def TestimonialsView(request):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=HOME_CONTROLLER.testimonials())


# 11. In their words = random reviews
@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def RandomReviewsView(request):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=HOME_CONTROLLER.random_reviews())
