"""Explore page section views (sync DRF).

Canonical responder stack (task 20): @exceptionHandler(responseFunc=ServerResponse,
errorMessage=...) wraps each view — the decorator maps controller NotFound_/
PermissionError_/Conflict_ to 410/403/409 and any other exception to a clean envelope;
views return ServerResponse(...) directly (no local _ok/_err wrappers, no per-view try/except)."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.decorators.ViewDecorator import exceptionHandler
from app_ib.Controllers.Engine.ExploreController import ENGINE_EXPLORE_CONTROLLER, create_project


# search-query cards (redirect to home + add filter on the FE)
@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ExploreSearchCardsView(request):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=ENGINE_EXPLORE_CONTROLLER.search_cards())


# 1. Editors pick
@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def EditorsPickView(request):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=ENGINE_EXPLORE_CONTROLLER.editors_pick())


# 2. Design ideas (architect projects, any architect)
@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def DesignIdeasView(request):
    architect_id = request.GET.get("architectId")
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=ENGINE_EXPLORE_CONTROLLER.design_ideas(
                              architect_id=int(architect_id) if architect_id else None,
                              style=request.GET.get("style", ""), city=request.GET.get("city", "")))


# architect adds a project
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ProjectCreateView(request, architectId):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.project_created,
                          data=create_project(request.user, architectId, request.data))
