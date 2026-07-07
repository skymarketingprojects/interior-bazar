from asgiref.sync import sync_to_async
from typing import Any, Dict, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES

from app_ib.models import Subscription
from interior_admin.Controllers.Audit.AuditController import append_audit
from .Validators.PlansValidators import PlanUpdateSchema

# Price-affecting fields → editing them is level-3 (audited).
PRICE_FIELDS = {"amount", "payableAmount", "discountPercentage"}


def _plan_dict(s: Subscription) -> Dict[str, Any]:
    return {
        "id": s.id, "planFamily": s.planFamily, "entityType": s.entityType,
        "title": s.title, "subtitle": s.subtitle, "tier": s.tier,
        "amount": s.amount, "payableAmount": s.payableAmount,
        "discountPercentage": s.discountPercentage, "duration": s.duration,
        "tag": s.tag,
    }


class PlansController:

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def List(cls) -> Tuple[bool, Dict[str, Any]]:
        rows = await sync_to_async(list)(Subscription.objects.all().order_by("planFamily", "tier"))
        families: Dict[str, list] = {}
        for s in rows:
            families.setdefault(s.planFamily or "business", []).append(_plan_dict(s))
        return True, {"families": families, "plans": [_plan_dict(s) for s in rows]}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Update(cls, planId: int, payload: PlanUpdateSchema, actor=None) -> Tuple[bool, Dict[str, Any]]:
        s = await Subscription.objects.filter(id=planId).afirst()
        if s is None:
            return False, {"message": "Plan not found"}
        changed = []
        for field in ("title", "subtitle", "amount", "payableAmount", "discountPercentage", "duration", "tag"):
            val = getattr(payload, field)
            if val is not None and str(getattr(s, field)) != str(val):
                setattr(s, field, val)
                changed.append(field)
        await sync_to_async(s.save)()
        if set(changed) & PRICE_FIELDS:
            await append_audit(actor=actor, action='plan_price_updated', module_key='plans',
                               detail=f"plan={s.id} '{s.title}' changed={changed}")
        return True, _plan_dict(s)


PLANS_CONTROLLER = PlansController()
