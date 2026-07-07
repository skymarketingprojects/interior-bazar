from adrf.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.decorators.ViewDecorator import exceptionHandler

from interior_admin.Controllers.Weights.WeightsController import WEIGHTS_CONTROLLER
from interior_admin.Controllers.Weights.Validators.WeightsValidators import WeightsSchema
from interior_admin.Validators.adminValidators import hasAccess


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def WeightsView(request: Request):
    """GET /api/v1/admin/weights/ — current qualification signal→weight config.
    PUT /api/v1/admin/weights/ — set/merge weights. Super-admin, level-3 (audited)."""
    await hasAccess(request=request)
    if request.method == 'PUT':
        return await WEIGHTS_CONTROLLER.Set(payload=WeightsSchema(**request.data), actor=request.user)
    return await WEIGHTS_CONTROLLER.Get()
