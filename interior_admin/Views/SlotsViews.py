from adrf.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.decorators.ViewDecorator import exceptionHandler

from interior_admin.Controllers.Slots.SlotsController import SLOTS_CONTROLLER
from interior_admin.Controllers.Slots.Validators.SlotsValidators import SlotOverrideSchema
from interior_admin.Validators.adminValidators import hasAccess


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def SlotsGridView(request: Request):
    """GET /api/v1/admin/slots/ — full slot-inventory grid."""
    await hasAccess(request=request)
    return await SLOTS_CONTROLLER.Grid()


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def SlotOverrideView(request: Request, slotId: int):
    """PUT /api/v1/admin/slots/<id>/ — override capacity/holder/priority. Level-3."""
    await hasAccess(request=request)
    return await SLOTS_CONTROLLER.Override(slotId=slotId, payload=SlotOverrideSchema(**request.data), actor=request.user)
