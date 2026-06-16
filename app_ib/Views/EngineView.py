"""
EngineView — thin HTTP layer for the v2.1.0.0 discovery engine. Parses the
request, calls EngineController, wraps the result in ServerResponse.

Public reads + event tracking allow anonymous; saved/recently-viewed/notifications
require auth. Sync DRF views (test-client friendly).
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.EngineConfig import (
    ENTITY_TYPE, TRENDING_PERIOD, LEADERBOARD_PERIOD, LEADERBOARD_BOARD,
)
from app_ib.Controllers.Engine.EngineController import ENGINE_CONTROLLER

_OK = RESPONSE_CODES.success


def _ok(data, message="ok"):
    return ServerResponse(response=True, code=_OK, message=message, data=data)


def _bad(message="bad request"):
    return ServerResponse(response=False, code=RESPONSE_CODES.bad_request, message=message, data={})


# ----------------------- Trending -----------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def TrendingBusinessesView(request):
    period = request.GET.get("period", TRENDING_PERIOD.DAILY)
    city = request.GET.get("city", "")
    if period not in TRENDING_PERIOD.ALL:
        return _bad("invalid period")
    return _ok(ENGINE_CONTROLLER.trending_entities(ENTITY_TYPE.BUSINESS, period, city))


@api_view(["GET"])
@permission_classes([AllowAny])
def TrendingProductsView(request):
    period = request.GET.get("period", TRENDING_PERIOD.DAILY)
    return _ok(ENGINE_CONTROLLER.trending_entities(ENTITY_TYPE.PRODUCT, period, ""))


@api_view(["GET"])
@permission_classes([AllowAny])
def TrendingSearchesView(request):
    # Category fallback is ON by default so the trending-page searches panel never
    # renders empty: a sparse/empty searches board is topped up with business
    # categories. Pass ?fallback=0 (or false/none) to opt out and get raw searches.
    fallback = request.GET.get("fallback", "1") not in ("0", "false", "none")
    return _ok(ENGINE_CONTROLLER.trending_searches(category_fallback=fallback))


@api_view(["GET"])
@permission_classes([AllowAny])
def MomentumView(request):
    """Cross-entity momentum board — any entity type, ranked by trending."""
    return _ok(ENGINE_CONTROLLER.momentum())


@api_view(["GET"])
@permission_classes([AllowAny])
def CityPulseView(request):
    return _ok(ENGINE_CONTROLLER.city_pulse(request.GET.get("city", "")))


# ----------------------- Leaderboard -----------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def LeaderboardView(request):
    period = request.GET.get("period", LEADERBOARD_PERIOD.WEEKLY)
    board = request.GET.get("board", LEADERBOARD_BOARD.COMBINED)
    # optional ?entityTypes=product,service to filter+re-rank a subset board
    et_raw = request.GET.get("entityTypes", "")
    entity_types = [x.strip() for x in et_raw.split(",") if x.strip()] or None
    if period not in LEADERBOARD_PERIOD.ALL:
        return _bad("invalid period")
    return _ok(ENGINE_CONTROLLER.leaderboard(period, board, entity_types=entity_types))


# ----------------------- Discovery -----------------------
@api_view(["GET"])
@permission_classes([AllowAny])
def MostSavedView(request):
    return _ok(ENGINE_CONTROLLER.most_saved())


@api_view(["GET"])
@permission_classes([AllowAny])
def BehindTheTrendView(request):
    return _ok(ENGINE_CONTROLLER.behind_the_trend())


# ----------------------- Completion -----------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def CompletionView(request, entityType, objectId):
    if entityType not in ENTITY_TYPE.COMPLETION:
        return _bad("unsupported entity type")
    data = ENGINE_CONTROLLER.completion(entityType, objectId)
    if data is None:
        return ServerResponse(response=False, code=RESPONSE_CODES.not_exist,
                              message=RESPONSE_MESSAGES.resource_not_found
                              if hasattr(RESPONSE_MESSAGES, "resource_not_found") else "not found",
                              data={})
    return _ok(data)


# ----------------------- Events (fire-and-forget) -----------------------
@api_view(["POST"])
@permission_classes([AllowAny])
def TrackViewView(request):
    d = request.data
    et = d.get("entityType")
    if et not in ENTITY_TYPE.ALL or not d.get("objectId"):
        return _bad("entityType/objectId required")
    ENGINE_CONTROLLER.track_view(
        et, int(d["objectId"]), user=request.user, session_id=d.get("sessionId", ""),
        city=d.get("city", ""), state=d.get("state", ""), dwell_seconds=d.get("dwellSeconds"))
    return _ok({}, "tracked")


@api_view(["POST"])
@permission_classes([AllowAny])
def TrackClickView(request):
    d = request.data
    et = d.get("entityType")
    if et not in ENTITY_TYPE.ALL or not d.get("objectId") or not d.get("clickType"):
        return _bad("entityType/objectId/clickType required")
    ENGINE_CONTROLLER.track_click(et, int(d["objectId"]), d["clickType"],
                                  user=request.user, session_id=d.get("sessionId", ""))
    return _ok({}, "tracked")


@api_view(["POST"])
@permission_classes([AllowAny])
def TrackSearchView(request):
    d = request.data
    if not d.get("query"):
        return _bad("query required")
    sid = ENGINE_CONTROLLER.track_search(
        d["query"], int(d.get("resultCount", 0)), d.get("city", ""), d.get("state", ""),
        user=request.user, session_id=d.get("sessionId", ""))
    return _ok({"searchEventId": sid}, "tracked")


# ----------------------- Saved / Recently / Notifications -----------------------
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def SavedItemsView(request):
    if request.method == "POST":
        d = request.data
        et = d.get("entityType")
        if et not in ENTITY_TYPE.ALL or not d.get("objectId"):
            return _bad("entityType/objectId required")
        saved = ENGINE_CONTROLLER.toggle_saved(request.user, et, int(d["objectId"]))
        return _ok({"isSaved": saved},
                   RESPONSE_MESSAGES.success if hasattr(RESPONSE_MESSAGES, "success") else "ok")
    return _ok(ENGINE_CONTROLLER.list_saved(request.user))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def RecentlyViewedView(request):
    return _ok(ENGINE_CONTROLLER.recently_viewed(request.user))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def NotificationsView(request):
    return _ok(ENGINE_CONTROLLER.notifications(request.user))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def NotificationUnreadCountView(request):
    return _ok({"count": ENGINE_CONTROLLER.unread_count(request.user)})
