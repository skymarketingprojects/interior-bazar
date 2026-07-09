from asgiref.sync import sync_to_async
from typing import Any, Dict, List, Optional, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.EngineConfig import PLAN_STATUS
from app_ib.models import BusinessPlan, ShopPlan, ArchitectPlan, AutomationPlan

# family literal → (model, related entity fields to select). automation carries
# one nullable FK per entity type.
FAMILIES = {
    "business": (BusinessPlan, ("business",)),
    "shop": (ShopPlan, ("shop",)),
    "architect": (ArchitectPlan, ("architect",)),
    "automation": (AutomationPlan, ("business", "shop", "architect")),
}


def _amount_num(a) -> float:
    try:
        return float(str(a or "0").replace(",", "").strip() or 0)
    except (ValueError, TypeError):
        return 0.0


def _entity_name(p, family: str) -> Optional[str]:
    if family == "business":
        return p.business.businessName if p.business_id else None
    if family == "shop":
        return p.shop.name if p.shop_id else None
    if family == "architect":
        return p.architect.name if p.architect_id else None
    if family == "automation":
        if p.business_id:
            return p.business.businessName
        if p.shop_id:
            return p.shop.name
        if p.architect_id:
            return p.architect.name
    return None


def _row(p, family: str) -> Dict[str, Any]:
    return {
        "id": p.id, "family": family, "amount": p.amount, "status": p.status,
        "isActive": p.isActive,
        "user": p.user.username if p.user_id else None,
        "entityName": _entity_name(p, family),
        "planTitle": p.plan.title if p.plan_id else None,
        "expireDate": p.expireDate.isoformat() if p.expireDate else None,
    }


class SubsController:
    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def List(cls, family: str = None, status: str = None,
                   pageNo: int = 1, pageSize: int = 20) -> Tuple[bool, Dict[str, Any]]:
        pageNo = max(1, pageNo or 1)
        pageSize = min(100, max(1, pageSize or 20))
        # family scopes the analytics + list to one model; None/"all" aggregates 4.
        scope = [(family, *FAMILIES[family])] if family in FAMILIES else \
                [(f, m, ents) for f, (m, ents) in FAMILIES.items()]

        activeC = expiredC = pendingC = totalC = 0
        revenue = 0.0
        listTotal = 0
        merged: List = []
        for fam, model, ents in scope:
            base = model.objects.all()
            totalC += await base.acount()
            activeC += await base.filter(status=PLAN_STATUS.ACTIVE).acount()
            expiredC += await base.filter(status=PLAN_STATUS.EXPIRED).acount()
            pendingC += await base.filter(status=PLAN_STATUS.PENDING).acount()
            amts = await sync_to_async(list)(
                base.filter(status=PLAN_STATUS.ACTIVE).values_list("amount", flat=True))
            revenue += sum(_amount_num(a) for a in amts)

            lqs = model.objects.select_related("user", "plan", *ents)
            if status:
                lqs = lqs.filter(status=status)
            listTotal += await lqs.acount()
            # ponytail: cap 1000/family for the merged page window — dev-scale safe.
            rows = await sync_to_async(list)(lqs.order_by("-id")[:1000])
            merged.extend((p, fam) for p in rows)

        merged.sort(key=lambda pr: pr[0].id, reverse=True)
        start = (pageNo - 1) * pageSize
        page_rows = merged[start:start + pageSize]
        subs = await sync_to_async(lambda: [_row(p, fam) for p, fam in page_rows])()

        # MRR omitted deliberately: plan duration is a free-form Subscription.duration
        # string, not reliably parseable to months — do not fabricate (task 10).
        analytics = {
            "activeCount": activeC, "expiredCount": expiredC,
            "pendingCount": pendingC, "totalCount": totalC,
            "revenue": round(revenue, 2),
        }
        return True, {
            "subs": subs, "total": listTotal, "pageNo": pageNo, "pageSize": pageSize,
            "analytics": analytics, "family": family or "all",
        }


SUBS_CONTROLLER = SubsController()
