from asgiref.sync import sync_to_async
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Tuple

from django.core.cache import cache

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES

from app_ib.models import (Subscription, PlanBillingCycle, BusinessPlan, ShopPlan,
                           ArchitectPlan, AutomationPlan)
from interior_admin.Controllers.Audit.AuditController import append_audit
from .Validators.PlansValidators import PlanCreateSchema, PlanUpdateSchema

# Price-affecting fields → editing them is level-3 (audited).
PRICE_FIELDS = {"amount", "payableAmount", "discountPercentage"}


def _dec(val):
    """'₹53,099'/'53099'/53099 -> Decimal, else None (blank/garbage)."""
    if val is None:
        return None
    s = str(val).replace("₹", "").replace(",", "").strip()
    if not s:
        return None
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def _money_str(d):
    """Decimal -> clean string ('53099' not '53099.00'); None -> None."""
    if d is None:
        return None
    return str(int(d)) if d == d.to_integral_value() else str(d)

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


def _cycle_dict(c: PlanBillingCycle) -> Dict[str, Any]:
    return {
        "id": c.id, "durationMonths": c.durationMonths,
        "price": _money_str(c.price), "oldPrice": _money_str(c.oldPrice),
        "badgeLabel": c.badgeLabel or "", "isActive": c.isActive,
    }


def _plan_dict(s: Subscription) -> Dict[str, Any]:
    # Accesses s.billingCycles — call from a sync context (List prefetches;
    # the async mutators wrap it in sync_to_async).
    return {
        "id": s.id, "planFamily": s.planFamily, "entityType": s.entityType,
        "title": s.title, "subtitle": s.subtitle, "tier": s.tier,
        "amount": s.amount, "payableAmount": s.payableAmount,
        "discountPercentage": s.discountPercentage, "duration": s.duration,
        "tag": s.tag, "badge": s.badge, "badgeIcon": s.badgeIcon,
        "features": s.features or [], "isActive": s.isActive,
        "billingCycles": [_cycle_dict(c) for c in s.billingCycles.all().order_by("durationMonths")],
    }


# planFamily → the entityType whose purchase this plan unlocks. The checkout
# resolves a plan by entityType, so a plan created under the architect family
# MUST carry entityType 'architect' (previously everything defaulted to
# 'business', which made admin-created non-business plans unbuyable).
FAMILY_ENTITY = {"business": "business", "shop": "shop", "shops": "shop",
                 "architect": "architect", "architecture": "architect",
                 "automation": "automation"}


class PlansController:

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def List(cls) -> Tuple[bool, Dict[str, Any]]:
        # Admin sees ALL plans incl. archived (isActive in payload) — archive must
        # never hide a plan from admins or it could never be re-activated.
        # Soft-DELETED plans are hidden everywhere; purchased-plan FKs stay intact.
        # Build entirely in a sync context — _plan_dict reads s.billingCycles.
        def _build():
            rows = list(Subscription.objects.filter(is_delete=False)
                        .prefetch_related("billingCycles").order_by("planFamily", "tier"))
            families: Dict[str, list] = {}
            plans = []
            for s in rows:
                d = _plan_dict(s)
                families.setdefault(s.planFamily or "business", []).append(d)
                plans.append(d)
            return {"families": families, "plans": plans}
        return True, await sync_to_async(_build)()

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Create(cls, payload: PlanCreateSchema, actor=None) -> Tuple[bool, Dict[str, Any]]:
        family = (payload.planFamily or "").strip().lower()
        data = {
            "planFamily": payload.planFamily,
            # entityType drives which entity the purchase unlocks AND how the
            # checkout resolves the plan — derive it from the family.
            "entityType": payload.entityType or FAMILY_ENTITY.get(family, "business"),
            "title": payload.title or "",
            "subtitle": payload.subtitle or "",
            "amount": payload.amount or "",
            "payableAmount": payload.payableAmount or "",
            "discountPercentage": payload.discountPercentage or "",
            "duration": payload.duration or "",
            "tag": payload.tag or "",
            "badge": payload.badge or "",
            "badgeIcon": payload.badgeIcon or "",
            "services": payload.services or "",  # model field is non-nullable
            "isActive": True,  # new plans are live immediately (task e)
        }
        if payload.tier is not None:
            data["tier"] = payload.tier
        if payload.features is not None:
            data["features"] = _features_to_json(payload.features)
        s = await Subscription.objects.acreate(**data)
        # Optional cycles[] — create plan + its billing cycles in one call.
        for c in (payload.cycles or []):
            price = _dec(c.price)
            if c.durationMonths and price is not None:
                await PlanBillingCycle.objects.acreate(
                    plan_id=s.id, durationMonths=c.durationMonths, price=price,
                    oldPrice=_dec(c.oldPrice), badgeLabel=(c.badgeLabel or "")[:100],
                    isActive=True if c.isActive is None else bool(c.isActive))
        cache.delete(PUBLIC_PLANS_CACHE_KEY)
        await append_audit(actor=actor, action='plan_created', module_key='plans',
                           detail=f"plan={s.id} '{s.title}' family={s.planFamily}")
        return True, await sync_to_async(_plan_dict)(s)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Update(cls, planId: int, payload: PlanUpdateSchema, actor=None) -> Tuple[bool, Dict[str, Any]]:
        s = await Subscription.objects.filter(id=planId).afirst()
        if s is None:
            return False, {"message": "Plan not found"}
        changed = []
        for field in ("title", "subtitle", "amount", "payableAmount", "discountPercentage",
                      "duration", "tag", "badge", "badgeIcon", "tier"):
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
        return True, await sync_to_async(_plan_dict)(s)

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
        return True, await sync_to_async(_plan_dict)(s)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Delete(cls, planId: int, actor=None) -> Tuple[bool, Dict[str, Any]]:
        """Soft delete: hide the plan from admin + public without breaking the FK on
        already-purchased BusinessPlan/ShopPlan/ArchitectPlan/AutomationPlan rows —
        existing subscribers keep their entitlements until expiry."""
        s = await Subscription.objects.filter(id=planId, is_delete=False).afirst()
        if s is None:
            return False, {"message": "Plan not found"}
        s.is_delete = True
        s.isActive = False  # deleted plans are never buyable
        await sync_to_async(s.save)()
        cache.delete(PUBLIC_PLANS_CACHE_KEY)
        await append_audit(actor=actor, action='plan_deleted', module_key='plans',
                           detail=f"plan={s.id} '{s.title}' family={s.planFamily}")
        return True, {"id": planId, "deleted": True}

    # ── Billing cycles (task 30) — add/enable/disable a time·price option on a plan ──
    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def CreateCycle(cls, planId: int, payload, actor=None) -> Tuple[bool, Dict[str, Any]]:
        s = await Subscription.objects.filter(id=planId, is_delete=False).afirst()
        if s is None:
            return False, {"message": "Plan not found"}
        price = _dec(payload.price)
        if not payload.durationMonths or price is None:
            return False, {"message": "durationMonths and a valid price are required"}
        exists = await PlanBillingCycle.objects.filter(
            plan_id=planId, durationMonths=payload.durationMonths).aexists()
        if exists:
            return False, {"message": f"A {payload.durationMonths}-month cycle already exists"}
        c = await PlanBillingCycle.objects.acreate(
            plan_id=planId, durationMonths=payload.durationMonths, price=price,
            oldPrice=_dec(payload.oldPrice), badgeLabel=(payload.badgeLabel or "")[:100],
            isActive=True if payload.isActive is None else bool(payload.isActive))
        cache.delete(PUBLIC_PLANS_CACHE_KEY)
        # New price on the catalogue → level-3 audited like a plan price edit.
        await append_audit(actor=actor, action='plan_price_updated', module_key='plans',
                           detail=f"plan={planId} cycle_created {payload.durationMonths}mo ₹{_money_str(price)}")
        return True, _cycle_dict(c)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def UpdateCycle(cls, planId: int, cycleId: int, payload, actor=None) -> Tuple[bool, Dict[str, Any]]:
        c = await PlanBillingCycle.objects.filter(id=cycleId, plan_id=planId).afirst()
        if c is None:
            return False, {"message": "Cycle not found"}
        price_changed = False
        if payload.durationMonths is not None:
            c.durationMonths = payload.durationMonths
        if payload.price is not None:
            new_price = _dec(payload.price)
            if new_price is not None and new_price != c.price:
                c.price = new_price
                price_changed = True
        if payload.oldPrice is not None:
            c.oldPrice = _dec(payload.oldPrice)
        if payload.badgeLabel is not None:
            c.badgeLabel = (payload.badgeLabel or "")[:100]
        if payload.isActive is not None:
            c.isActive = bool(payload.isActive)
        await sync_to_async(c.save)()
        cache.delete(PUBLIC_PLANS_CACHE_KEY)
        if price_changed:
            await append_audit(actor=actor, action='plan_price_updated', module_key='plans',
                               detail=f"plan={planId} cycle={cycleId} price -> ₹{_money_str(c.price)}")
        return True, _cycle_dict(c)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def DeleteCycle(cls, planId: int, cycleId: int, actor=None) -> Tuple[bool, Dict[str, Any]]:
        """Hard-delete if the cycle was never purchased (no purchase row snapshotting
        this plan+duration); otherwise disable it (isActive=False) to keep history."""
        c = await PlanBillingCycle.objects.filter(id=cycleId, plan_id=planId).afirst()
        if c is None:
            return False, {"message": "Cycle not found"}
        months = c.durationMonths
        purchased = False
        for Model in (BusinessPlan, ShopPlan, ArchitectPlan, AutomationPlan):
            if await Model.objects.filter(plan_id=planId, durationMonths=months).aexists():
                purchased = True
                break
        if purchased:
            c.isActive = False
            await sync_to_async(c.save)()
            result = {"id": cycleId, "deleted": False, "disabled": True}
        else:
            await c.adelete()
            result = {"id": cycleId, "deleted": True}
        cache.delete(PUBLIC_PLANS_CACHE_KEY)
        await append_audit(actor=actor, action='plan_price_updated', module_key='plans',
                           detail=f"plan={planId} cycle={cycleId} {'disabled' if purchased else 'deleted'}")
        return True, result


PLANS_CONTROLLER = PlansController()
