"""
EngineView — thin HTTP layer for the v2.1.0.0 discovery engine. Parses the
request, calls EngineController, wraps the result in ServerResponse.

Public reads + event tracking allow anonymous; saved/recently-viewed/notifications
require auth. Sync DRF views (test-client friendly).

Canonical responder stack (task 20): @exceptionHandler(responseFunc=ServerResponse,
errorMessage=...) wraps each view — the decorator maps engine NotFound_/PermissionError_/
Conflict_ to 410/403/409 and any other exception to a clean envelope; views return
ServerResponse(...) directly with RESPONSE_CODES/RESPONSE_MESSAGES constants (no local wrappers).
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.decorators.ViewDecorator import exceptionHandler
from app_ib.Utils.EngineConfig import (
    ENTITY_TYPE, TRENDING_PERIOD, LEADERBOARD_PERIOD, LEADERBOARD_BOARD,
)
from app_ib.Controllers.Engine.EngineController import ENGINE_CONTROLLER


# ----------------------- Trending -----------------------
@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def TrendingBusinessesView(request):
    period = request.GET.get("period", TRENDING_PERIOD.DAILY)
    city = request.GET.get("city", "")
    if period not in TRENDING_PERIOD.ALL:
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request, message=RESPONSE_MESSAGES.invalid_period, data={})
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=ENGINE_CONTROLLER.trending_entities(ENTITY_TYPE.BUSINESS, period, city))


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def TrendingProductsView(request):
    period = request.GET.get("period", TRENDING_PERIOD.DAILY)
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=ENGINE_CONTROLLER.trending_entities(ENTITY_TYPE.PRODUCT, period, ""))


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def TrendingSearchesView(request):
    # Category fallback is ON by default so the trending-page searches panel never
    # renders empty: a sparse/empty searches board is topped up with business
    # categories. Pass ?fallback=0 (or false/none) to opt out and get raw searches.
    fallback = request.GET.get("fallback", "1") not in ("0", "false", "none")
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=ENGINE_CONTROLLER.trending_searches(category_fallback=fallback))


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def MomentumView(request):
    """Cross-entity momentum board — any entity type, ranked by trending."""
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=ENGINE_CONTROLLER.momentum())


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def CityPulseView(request):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=ENGINE_CONTROLLER.city_pulse(request.GET.get("city", "")))


# ----------------------- Leaderboard -----------------------
@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def LeaderboardView(request):
    period = request.GET.get("period", LEADERBOARD_PERIOD.WEEKLY)
    board = request.GET.get("board", LEADERBOARD_BOARD.COMBINED)
    # optional ?entityTypes=product,service to filter+re-rank a subset board
    et_raw = request.GET.get("entityTypes", "")
    entity_types = [x.strip() for x in et_raw.split(",") if x.strip()] or None
    if period not in LEADERBOARD_PERIOD.ALL:
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request, message=RESPONSE_MESSAGES.invalid_period, data={})
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=ENGINE_CONTROLLER.leaderboard(period, board, entity_types=entity_types))


# ----------------------- Discovery -----------------------
@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def MostSavedView(request):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=ENGINE_CONTROLLER.most_saved())


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def BehindTheTrendView(request):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=ENGINE_CONTROLLER.behind_the_trend())


# ----------------------- Completion -----------------------
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def CompletionView(request, entityType, objectId):
    if entityType not in ENTITY_TYPE.COMPLETION:
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request,
                              message=RESPONSE_MESSAGES.unsupported_entity_type_plain, data={})
    data = ENGINE_CONTROLLER.completion(entityType, objectId)
    if data is None:
        return ServerResponse(response=False, code=RESPONSE_CODES.not_exist,
                              message=RESPONSE_MESSAGES.resource_not_found, data={})
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=data)


# ----------------------- Events (fire-and-forget) -----------------------
@api_view(["POST"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def TrackViewView(request):
    d = request.data
    et = d.get("entityType")
    if et not in ENTITY_TYPE.ALL or not d.get("objectId"):
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request, message=RESPONSE_MESSAGES.entity_object_id_required, data={})
    ENGINE_CONTROLLER.track_view(
        et, int(d["objectId"]), user=request.user, session_id=d.get("sessionId", ""),
        city=d.get("city", ""), state=d.get("state", ""), dwell_seconds=d.get("dwellSeconds"))
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.tracked, data={})


@api_view(["POST"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def TrackClickView(request):
    d = request.data
    et = d.get("entityType")
    if et not in ENTITY_TYPE.ALL or not d.get("objectId") or not d.get("clickType"):
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request, message=RESPONSE_MESSAGES.entity_object_click_required, data={})
    ENGINE_CONTROLLER.track_click(et, int(d["objectId"]), d["clickType"],
                                  user=request.user, session_id=d.get("sessionId", ""))
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.tracked, data={})


@api_view(["POST"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def TrackSearchView(request):
    d = request.data
    if not d.get("query"):
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request, message=RESPONSE_MESSAGES.search_query_required, data={})
    sid = ENGINE_CONTROLLER.track_search(
        d["query"], int(d.get("resultCount", 0)), d.get("city", ""), d.get("state", ""),
        user=request.user, session_id=d.get("sessionId", ""))
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.tracked, data={"searchEventId": sid})


# ----------------------- Saved / Recently / Notifications -----------------------
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def SavedItemsView(request):
    if request.method == "POST":
        d = request.data
        et = d.get("entityType")
        if et not in ENTITY_TYPE.ALL or not d.get("objectId"):
            return ServerResponse(response=False, code=RESPONSE_CODES.bad_request, message=RESPONSE_MESSAGES.entity_object_id_required, data={})
        saved = ENGINE_CONTROLLER.toggle_saved(request.user, et, int(d["objectId"]))
        return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data={"isSaved": saved})
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=ENGINE_CONTROLLER.list_saved(request.user))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def RecentlyViewedView(request):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=ENGINE_CONTROLLER.recently_viewed(request.user))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def RecentlyViewedExportView(request):
    """GET /engine/recently-viewed/export/ — downloadable CSV of the caller's
    own recently-viewed history. Same source query as RecentlyViewedView
    (recently_viewed_export_rows mirrors recently_viewed's query/ordering),
    trimmed to two safe columns: Name, Viewed at (no ids/objectId/slug/
    entityType — nothing that could leak internal keys).

    Deliberate exception to the ServerResponse JSON envelope: this returns a
    raw Django HttpResponse (text/csv, Content-Disposition attachment), the
    same "raw response instead of ServerResponse" precedent already used by
    UserStreamTokenView (EngineGapsView.py) for its SSE StreamingHttpResponse.
    Left UNDECORATED on purpose (task 20).
    """
    import csv
    from django.http import HttpResponse
    from app_ib.Utils.Names import NAMES

    rows = ENGINE_CONTROLLER.recently_viewed_export_rows(request.user)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="recently-viewed-history.csv"'
    writer = csv.writer(response)
    writer.writerow(["Name", "Viewed at"])
    for name, viewed_at in rows:
        writer.writerow([name, viewed_at.strftime(NAMES.DMY_12M) if viewed_at else ""])
    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def NotificationsView(request):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=ENGINE_CONTROLLER.notifications(request.user))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def NotificationUnreadCountView(request):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data={"count": ENGINE_CONTROLLER.unread_count(request.user)})
