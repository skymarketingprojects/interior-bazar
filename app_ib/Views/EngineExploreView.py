"""Explore page section views (sync DRF)."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Controllers.Engine.ExploreController import ENGINE_EXPLORE_CONTROLLER, create_project
from app_ib.Controllers.Engine.CrudController import NotFound_, PermissionError_, Conflict_


def _ok(data, msg="ok"):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=msg, data=data)


def _err(e):
    if isinstance(e, NotFound_):
        return ServerResponse(response=False, code=RESPONSE_CODES.not_exist, message=str(e), data={})
    if isinstance(e, PermissionError_):
        return ServerResponse(response=False, code=RESPONSE_CODES.forbidden, message=str(e), data={})
    return ServerResponse(response=False, code=RESPONSE_CODES.error, message=str(e), data={})


# search-query cards (redirect to home + add filter on the FE)
@api_view(["GET"])
@permission_classes([AllowAny])
def ExploreSearchCardsView(request):
    return _ok(ENGINE_EXPLORE_CONTROLLER.search_cards())


# 1. Editors pick
@api_view(["GET"])
@permission_classes([AllowAny])
def EditorsPickView(request):
    return _ok(ENGINE_EXPLORE_CONTROLLER.editors_pick())


# 2. Design ideas (architect projects, any architect)
@api_view(["GET"])
@permission_classes([AllowAny])
def DesignIdeasView(request):
    architect_id = request.GET.get("architectId")
    return _ok(ENGINE_EXPLORE_CONTROLLER.design_ideas(
        architect_id=int(architect_id) if architect_id else None,
        style=request.GET.get("style", ""), city=request.GET.get("city", "")))


# architect adds a project
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ProjectCreateView(request, architectId):
    try:
        return _ok(create_project(request.user, architectId, request.data), "Project created")
    except Exception as e:
        return _err(e)
