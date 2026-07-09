from adrf.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.decorators.ViewDecorator import exceptionHandler

from interior_admin.Controllers.Businesses.BusinessesController import BUSINESSES_CONTROLLER
from interior_admin.Controllers.Businesses.Validators.BusinessesValidators import BusinessListFilters
from interior_admin.Validators.adminValidators import hasAccess


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def BusinessesListView(request: Request):
    """GET /api/v1/admin/businesses/ — businesses, paginated + search."""
    await hasAccess(request=request)
    return await BUSINESSES_CONTROLLER.List(queryParams=BusinessListFilters(**request.query_params.dict()))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def BusinessModerationView(request: Request):
    """GET /api/v1/admin/businesses/moderation/ — Catalog & Trust moderation view
    (profile score + catalog/review counts)."""
    await hasAccess(request=request)
    return await BUSINESSES_CONTROLLER.Moderation(queryParams=BusinessListFilters(**request.query_params.dict()))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def BusinessToggleVerifiedView(request: Request, businessId: int):
    """POST /api/v1/admin/businesses/<id>/toggle-verified/ — flip IB-verified badge."""
    await hasAccess(request=request)
    return await BUSINESSES_CONTROLLER.ToggleVerified(businessId=businessId, actor=request.user)
