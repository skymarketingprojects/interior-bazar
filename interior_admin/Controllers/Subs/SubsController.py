from asgiref.sync import sync_to_async
from typing import Any, Dict, List, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.models import BusinessPlan, ShopPlan, ArchitectPlan, AutomationPlan


def _row(p, family: str) -> Dict[str, Any]:
    return {
        "id": p.id, "family": family, "amount": p.amount, "status": p.status,
        "isActive": p.isActive, "user": p.user.username if p.user_id else None,
        "expireDate": p.expireDate.isoformat() if p.expireDate else None,
    }


class SubsController:
    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def List(cls, status: str = None) -> Tuple[bool, Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for model, fam in ((BusinessPlan, "business"), (ShopPlan, "shop"),
                           (ArchitectPlan, "architect"), (AutomationPlan, "automation")):
            qs = model.objects.select_related("user")
            if status:
                qs = qs.filter(status=status)
            rows = await sync_to_async(list)(qs.order_by("-id")[:200])
            out.extend(_row(p, fam) for p in rows)
        out.sort(key=lambda r: r["id"], reverse=True)
        return True, {"subs": out, "total": len(out)}


SUBS_CONTROLLER = SubsController()
