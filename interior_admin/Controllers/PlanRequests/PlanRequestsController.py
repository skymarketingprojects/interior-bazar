from asgiref.sync import sync_to_async
from django.db.models import Q
from typing import Any, Dict, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.models import (
    PlanQuery, Subscription, BusinessPlan, ShopPlan, ArchitectPlan, AutomationPlan,
)
from app_ib.Controllers.Plans.Tasks.PlanTasks import PLAN_TASKS
from interior_admin.Controllers.Audit.AuditController import append_audit

# entityType → (plan model, PLAN_TASKS create method, activate method)
FAMILY_TASKS = {
    "business": (BusinessPlan, "CreateBusinessPlan", "ActivateBusinessPlan"),
    "shop": (ShopPlan, "CreateShopPlan", "ActivateShopPlan"),
    "architect": (ArchitectPlan, "CreateArchitectPlan", "ActivateArchitectPlan"),
    "automation": (AutomationPlan, "CreateAutomationPlan", "ActivateAutomationPlan"),
}


def _pq(p: PlanQuery) -> Dict[str, Any]:
    return {"id": p.id, "plan": p.plan, "name": p.name, "email": p.email, "phone": p.phone,
            "state": p.state, "stage": p.stage, "transactionId": p.transactionId,
            "createdAt": p.timestamp.isoformat() if p.timestamp else ""}


class PlanRequestsController:
    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def List(cls, stage: str = None, pageNo: int = 1, pageSize: int = 20) -> Tuple[bool, Dict[str, Any]]:
        filters = Q()
        if stage:
            filters &= Q(stage=stage)
        pageNo = max(1, pageNo or 1); pageSize = min(100, max(1, pageSize or 20))
        start = (pageNo - 1) * pageSize
        qs = PlanQuery.objects.filter(filters).order_by("-id")
        total = await qs.acount()
        rows = await sync_to_async(list)(qs[start:start + pageSize])
        return True, {"requests": [_pq(p) for p in rows], "total": total, "pageNo": pageNo, "pageSize": pageSize}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def SetStage(cls, requestId: int, stage: str, actor=None) -> Tuple[bool, Dict[str, Any]]:
        p = await PlanQuery.objects.filter(id=requestId).afirst()
        if p is None:
            return False, {"message": "Plan request not found"}
        p.stage = stage
        await sync_to_async(p.save)()
        await append_audit(actor=actor, action=f"plan_request_{stage}", module_key="plan-requests", detail=f"request={p.id}")
        return True, _pq(p)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Verify(cls, requestId: int, subscriptionId: int, entityType: str, actor=None) -> Tuple[bool, Dict[str, Any]]:
        """Verify the manual payment + actually GRANT the plan (Payments-equivalent).
        PlanQuery.plan is a free-text label, so the admin picks the real Subscription
        + entity family. Creates the entity plan for the user then activates it
        (status ACTIVE + flips the user to seller), and closes the request."""
        p = await PlanQuery.objects.select_related("user").filter(id=requestId).afirst()
        if p is None:
            return False, {"message": "Plan request not found"}
        if not p.user_id:
            return False, {"message": "Request has no linked user to grant the plan to"}
        if entityType not in FAMILY_TASKS:
            return False, {"message": "Invalid entity type"}
        plan = await Subscription.objects.filter(id=subscriptionId).afirst()
        if plan is None:
            return False, {"message": "Subscription not found"}

        Model, create_name, activate_name = FAMILY_TASKS[entityType]
        created = await getattr(PLAN_TASKS, create_name)(plan=plan, user=p.user, transectionId=p.transactionId)
        if not created:
            return False, {"message": "Could not create the plan"}
        # Create*Plan returns a dict — fetch the just-created row to activate it.
        inst = await Model.objects.filter(user=p.user, transactionId=p.transactionId).order_by("-id").afirst()
        if inst is None:
            return False, {"message": "Created plan row not found"}
        await getattr(PLAN_TASKS, activate_name)(inst)

        p.stage = "4"
        await sync_to_async(p.save)()
        await append_audit(actor=actor, action="plan_request_verified", module_key="plan-requests",
                           detail=f"request={p.id} sub={subscriptionId} entity={entityType} plan={inst.id}")
        return True, _pq(p)


PLAN_REQUESTS_CONTROLLER = PlanRequestsController()
