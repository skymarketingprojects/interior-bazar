from asgiref.sync import sync_to_async
from django.db.models import Q
from typing import Any, Dict, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES

from app_ib.models import Business
from interior_admin.Controllers.Audit.AuditController import append_audit
from .Validators.BusinessesValidators import BusinessListFilters


def _biz_dict(b: Business) -> Dict[str, Any]:
    return {"id": b.id, "businessName": b.businessName, "isVerified": b.isVerified,
            "owner": b.user.username if b.user_id else None}


class BusinessesController:

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def List(cls, queryParams: BusinessListFilters) -> Tuple[bool, Dict[str, Any]]:
        filters = Q()
        if queryParams.search:
            filters &= Q(businessName__icontains=queryParams.search)
        pageNo = max(1, queryParams.pageNo or 1)
        pageSize = min(100, max(1, queryParams.pageSize or 20))
        start = (pageNo - 1) * pageSize
        qs = Business.objects.filter(filters).select_related("user").order_by("-id")
        total = await qs.acount()
        rows = await sync_to_async(list)(qs[start:start + pageSize])
        return True, {"businesses": [_biz_dict(b) for b in rows], "total": total, "pageNo": pageNo, "pageSize": pageSize}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def ToggleVerified(cls, businessId: int, actor=None) -> Tuple[bool, Dict[str, Any]]:
        b = await Business.objects.select_related("user").filter(id=businessId).afirst()
        if b is None:
            return False, {"message": "Business not found"}
        b.isVerified = not b.isVerified
        await sync_to_async(b.save)()
        await append_audit(actor=actor, action=("business_verified" if b.isVerified else "business_unverified"),
                           module_key="businesses", detail=f"business={b.id} {b.businessName}")
        return True, _biz_dict(b)


BUSINESSES_CONTROLLER = BusinessesController()
