from adrf.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.decorators.ViewDecorator import exceptionHandler

from interior_admin.Controllers.Plans.PlansController import PLANS_CONTROLLER
from interior_admin.Controllers.Plans.Validators.PlansValidators import PlanUpdateSchema
from interior_admin.Validators.adminValidators import hasAccess


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def PlansListView(request: Request):
    """GET /api/v1/admin/plans/ — pricing catalogue (Subscription) grouped by family."""
    await hasAccess(request=request)
    return await PLANS_CONTROLLER.List()


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def PlanUpdateView(request: Request, planId: int):
    """PUT /api/v1/admin/plans/<id>/ — edit a plan; price edits are level-3 (audited)."""
    await hasAccess(request=request)
    return await PLANS_CONTROLLER.Update(planId=planId, payload=PlanUpdateSchema(**request.data), actor=request.user)
