from adrf.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.decorators.ViewDecorator import exceptionHandler

from interior_admin.Controllers.Buyers.BuyersController import BUYERS_CONTROLLER
from interior_admin.Controllers.Buyers.Validators.BuyersValidators import BuyerListFilters
from interior_admin.Validators.adminValidators import hasAccess


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def BuyersListView(request: Request):
    """GET /api/v1/admin/buyers/ — buyers (type=user), paginated + search."""
    await hasAccess(request=request)
    return await BUYERS_CONTROLLER.List(queryParams=BuyerListFilters(**request.query_params.dict()))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def BuyerToggleView(request: Request, buyerId: int):
    """POST /api/v1/admin/buyers/<id>/toggle/ — block / activate a buyer."""
    await hasAccess(request=request)
    return await BUYERS_CONTROLLER.Toggle(buyerId=buyerId, actor=request.user)
