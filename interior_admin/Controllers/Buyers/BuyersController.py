from asgiref.sync import sync_to_async
from django.db.models import Q
from typing import Any, Dict, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES

from app_ib.models import CustomUser
from interior_admin.Controllers.Audit.AuditController import append_audit
from .Validators.BuyersValidators import BuyerListFilters

BUYER_TYPE = "user"


def _buyer_dict(u: CustomUser) -> Dict[str, Any]:
    return {"id": u.id, "username": u.username, "type": u.type,
            "isActive": u.is_active, "isVerified": u.isVerified,
            "joinedAt": u.timestamp.isoformat() if u.timestamp else ""}


class BuyersController:

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def List(cls, queryParams: BuyerListFilters) -> Tuple[bool, Dict[str, Any]]:
        filters = Q(type=BUYER_TYPE, is_delete=False)
        if queryParams.search:
            filters &= Q(username__icontains=queryParams.search)
        pageNo = max(1, queryParams.pageNo or 1)
        pageSize = min(100, max(1, queryParams.pageSize or 20))
        start = (pageNo - 1) * pageSize
        qs = CustomUser.objects.filter(filters).order_by("-timestamp")
        total = await qs.acount()
        rows = await sync_to_async(list)(qs[start:start + pageSize])
        return True, {"buyers": [_buyer_dict(u) for u in rows], "total": total, "pageNo": pageNo, "pageSize": pageSize}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Toggle(cls, buyerId: int, actor=None) -> Tuple[bool, Dict[str, Any]]:
        u = await CustomUser.objects.filter(id=buyerId, type=BUYER_TYPE).afirst()
        if u is None:
            return False, {"message": "Buyer not found"}
        u.is_active = not u.is_active
        await sync_to_async(u.save)()
        await append_audit(actor=actor, action=("buyer_activated" if u.is_active else "buyer_blocked"),
                           module_key="buyers", detail=f"buyer={u.id} {u.username}")
        return True, _buyer_dict(u)


BUYERS_CONTROLLER = BuyersController()
