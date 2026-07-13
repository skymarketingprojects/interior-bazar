from adrf.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.decorators.ViewDecorator import exceptionHandler

from interior_admin.Controllers.Plans.PlansController import PLANS_CONTROLLER
from interior_admin.Controllers.Plans.Validators.PlansValidators import (
    PlanCreateSchema, PlanUpdateSchema, PlanArchiveSchema,
    PlanCycleCreateSchema, PlanCycleUpdateSchema,
)
from interior_admin.Validators.adminValidators import hasAccess


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def PlansListView(request: Request):
    """GET  /api/v1/admin/plans/ — catalogue (Subscription) grouped by family (all, incl. archived).
    POST /api/v1/admin/plans/ — create a plan (isActive=true, audited)."""
    await hasAccess(request=request)
    if request.method == 'POST':
        return await PLANS_CONTROLLER.Create(payload=PlanCreateSchema(**request.data), actor=request.user)
    return await PLANS_CONTROLLER.List()


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def PlanUpdateView(request: Request, planId: int):
    """PUT    /api/v1/admin/plans/<id>/ — edit a plan; price edits are level-3 (audited).
    DELETE /api/v1/admin/plans/<id>/ — soft delete: hidden from admin + public, never
    buyable again; already-purchased plan rows keep their FK and stay active."""
    await hasAccess(request=request)
    if request.method == 'DELETE':
        return await PLANS_CONTROLLER.Delete(planId=planId, actor=request.user)
    return await PLANS_CONTROLLER.Update(planId=planId, payload=PlanUpdateSchema(**request.data), actor=request.user)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def PlanArchiveView(request: Request, planId: int):
    """POST /api/v1/admin/plans/<id>/archive/ {isActive} — toggle public visibility (audited).
    isActive=false archives (hidden from buyers, still visible to admins); true re-activates."""
    await hasAccess(request=request)
    payload = PlanArchiveSchema(**request.data)
    return await PLANS_CONTROLLER.SetActive(planId=planId, isActive=payload.isActive, actor=request.user)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def PlanCyclesView(request: Request, planId: int):
    """POST /api/v1/admin/plans/<id>/cycles/ — add a billing cycle (price/duration) to a
    plan. New price on the catalogue → level-3 audited."""
    await hasAccess(request=request)
    return await PLANS_CONTROLLER.CreateCycle(
        planId=planId, payload=PlanCycleCreateSchema(**request.data), actor=request.user)


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def PlanCycleDetailView(request: Request, planId: int, cycleId: int):
    """PUT    /api/v1/admin/plans/<id>/cycles/<cycleId>/ — edit a cycle (price edits audited).
    DELETE /api/v1/admin/plans/<id>/cycles/<cycleId>/ — hard delete if never purchased,
    else disable (isActive=False)."""
    await hasAccess(request=request)
    if request.method == 'DELETE':
        return await PLANS_CONTROLLER.DeleteCycle(planId=planId, cycleId=cycleId, actor=request.user)
    return await PLANS_CONTROLLER.UpdateCycle(
        planId=planId, cycleId=cycleId, payload=PlanCycleUpdateSchema(**request.data), actor=request.user)
