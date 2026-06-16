"""Home-page section views (sync DRF). Mostly public; 'for you' personalizes when
a JWT is present but still works anonymously (city-only)."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.EngineConfig import ENTITY_TYPE, HOME_FILTER
from app_ib.Controllers.Engine.HomeController import HOME_CONTROLLER


def _ok(data):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message="ok", data=data)


def _user(request):
    u = getattr(request, "user", None)
    return u if (u and u.is_authenticated) else None


# 1. Trending reels
@api_view(["GET"])
@permission_classes([AllowAny])
def ReelsView(request):
    return _ok(HOME_CONTROLLER.reels())


# 2/3/4/7. For-you recommendations (business/product/service/catelogue)
# Optional params (all additive — omit them and the response is unchanged):
#   filter=near_me|open_now|verified|top_rated  (basic pill from home/filters/)
#   categoryId=<BusinessCategory id>            (category pill from home/filters/)
#   lat/lng  — when a filter/category is active these enable the ~100km radius
#              (haversine) restriction; with no filter they're inert (no geo).
#   radiusKm — override the default for-you radius (HOME_FILTER.FORYOU_RADIUS_KM).
@api_view(["GET"])
@permission_classes([AllowAny])
def ForYouView(request, entityType):
    if entityType not in (ENTITY_TYPE.BUSINESS, ENTITY_TYPE.PRODUCT,
                          ENTITY_TYPE.SERVICE, ENTITY_TYPE.CATELOGUE):
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request,
                              message="unsupported entityType", data={})
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
    return _ok(HOME_CONTROLLER.recommend(entityType, user=_user(request),
                                         city=request.GET.get("city", ""),
                                         filter_code=filter_code,
                                         category_id=category_id,
                                         lat=lat, lng=lng, radius_km=radius_km))


# 0. Home filter bar — basic pills (with icons) + personalized category pills.
# AllowAny: anonymous users get the platform-popular categories; a valid JWT
# (resolved by _user, same pattern as ForYouView) personalizes from history.
@api_view(["GET"])
@permission_classes([AllowAny])
def HomeFiltersView(request):
    return _ok(HOME_CONTROLLER.home_filters(user=_user(request)))


# 5. Verified business = architects
@api_view(["GET"])
@permission_classes([AllowAny])
def ArchitectsRecommendedView(request):
    return _ok(HOME_CONTROLLER.recommend_architects(user=_user(request),
                                                    city=request.GET.get("city", "")))


# 6. Shops near you
@api_view(["GET"])
@permission_classes([AllowAny])
def ShopsNearbyView(request):
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    radius = request.GET.get("radius")
    return _ok(HOME_CONTROLLER.nearby_shops(
        float(lat) if lat else None, float(lng) if lng else None,
        float(radius) if radius else None, city=request.GET.get("city", "")))


# 9. Video stories = testimonials
@api_view(["GET"])
@permission_classes([AllowAny])
def TestimonialsView(request):
    return _ok(HOME_CONTROLLER.testimonials())


# 11. In their words = random reviews
@api_view(["GET"])
@permission_classes([AllowAny])
def RandomReviewsView(request):
    return _ok(HOME_CONTROLLER.random_reviews())
