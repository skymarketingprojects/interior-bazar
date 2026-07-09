from asgiref.sync import sync_to_async
from typing import Any, Dict, List, Tuple

from django.core.cache import cache

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES

from app_ib.models import Subscription
from interior_admin.Controllers.Audit.AuditController import append_audit
from .Validators.PlansValidators import PlanCreateSchema, PlanUpdateSchema

# Price-affecting fields → editing them is level-3 (audited).
PRICE_FIELDS = {"amount", "payableAmount", "discountPercentage"}

# Public buyer-facing plan cache (app_ib SubscriptionController). Every admin
# mutation must drop it or archive/edit is invisible to buyers for up to 24h.
PUBLIC_PLANS_CACHE_KEY = "subscription_plans_list"


def _features_to_json(features) -> List[Dict[str, str]]:
    """Normalise a features payload (list of strings or {text} dicts) → [{text}]."""
    out: List[Dict[str, str]] = []
    for f in features or []:
        text = f.get("text", "") if isinstance(f, dict) else f
        text = str(text).strip()
        if text:
            out.append({"text": text})
    return out


def _plan_dict(s: Subscription) -> Dict[str, Any]:
    return {
        "id": s.id, "planFamily": s.planFamily, "entityType": s.entityType,
        "title": s.title, "subtitle": s.subtitle, "tier": s.tier,
        "amount": s.amount, "payableAmount": s.payableAmount,
        "discountPercentage": s.discountPercentage, "duration": s.duration,
        "tag": s.tag, "features": s.features or [], "isActive": s.isActive,
    }


class PlansController:

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def List(cls) -> Tuple[bool, Dict[str, Any]]:
        # Admin sees ALL plans incl. archived (isActive in payload) — archive must
        # never hide a plan from admins or it could never be re-activated.
        rows = await sync_to_async(list)(Subscription.objects.all().order_by("planFamily", "tier"))
        families: Dict[str, list] = {}
        for s in rows:
            families.setdefault(s.planFamily or "business", []).append(_plan_dict(s))
        return True, {"families": families, "plans": [_plan_dict(s) for s in rows]}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Create(cls, payload: PlanCreateSchema, actor=None) -> Tuple[bool, Dict[str, Any]]:
        data = {
            "planFamily": payload.planFamily,
            "entityType": payload.entityType or "business",
            "title": payload.title or "",
            "subtitle": payload.subtitle or "",
            "amount": payload.amount or "",
            "payableAmount": payload.payableAmount or "",
            "discountPercentage": payload.discountPercentage or "",
            "duration": payload.duration or "",
            "tag": payload.tag or "",
            "services": payload.services or "",  # model field is non-nullable
            "isActive": True,  # new plans are live immediately (task e)
        }
        if payload.tier is not None:
            data["tier"] = payload.tier
        if payload.features is not None:
            data["features"] = _features_to_json(payload.features)
        s = await Subscription.objects.acreate(**data)
        cache.delete(PUBLIC_PLANS_CACHE_KEY)
        await append_audit(actor=actor, action='plan_created', module_key='plans',
                           detail=f"plan={s.id} '{s.title}' family={s.planFamily}")
        return True, _plan_dict(s)

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
        if payload.features is not None:
            s.features = _features_to_json(payload.features)
            changed.append("features")
        await sync_to_async(s.save)()
        cache.delete(PUBLIC_PLANS_CACHE_KEY)
        if set(changed) & PRICE_FIELDS:
            await append_audit(actor=actor, action='plan_price_updated', module_key='plans',
                               detail=f"plan={s.id} '{s.title}' changed={changed}")
        return True, _plan_dict(s)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def SetActive(cls, planId: int, isActive: bool, actor=None) -> Tuple[bool, Dict[str, Any]]:
        s = await Subscription.objects.filter(id=planId).afirst()
        if s is None:
            return False, {"message": "Plan not found"}
        s.isActive = bool(isActive)
        await sync_to_async(s.save)()
        cache.delete(PUBLIC_PLANS_CACHE_KEY)
        action = 'plan_activated' if s.isActive else 'plan_archived'
        await append_audit(actor=actor, action=action, module_key='plans',
                           detail=f"plan={s.id} '{s.title}' isActive={s.isActive}")
        return True, _plan_dict(s)


PLANS_CONTROLLER = PlansController()
