from asgiref.sync import sync_to_async
from django.db.models import Q, Prefetch
from typing import Any, Dict, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES

from app_ib.models import Business, BusinessPlan
from interior_admin.Controllers.Audit.AuditController import append_audit
from .Validators.BusinessesValidators import BusinessListFilters


def _biz_dict(b: Business) -> Dict[str, Any]:
    # Reverse O2O business_location via hasattr-guard (a business without a
    # location row shouldn't raise). Active plan comes from the List prefetch
    # (_active_plans); absent on the single-row ToggleVerified path → inactive.
    city = b.business_location.city if hasattr(b, "business_location") and b.business_location else ""
    active_plans = getattr(b, "_active_plans", None)
    active = active_plans[0] if active_plans else None
    return {
        "id": b.id, "businessName": b.businessName,
        "owner": b.user.username if b.user_id else None,
        "location": city or "",
        "isVerified": b.isVerified,
        # "active" = holds an active business plan (scoped to BusinessPlan).
        "status": "active" if active else "inactive",
        "planName": (active.plan.title if active.plan else "") if active else "",
        "planExpireAt": active.expireDate.isoformat() if active and active.expireDate else None,
        # Verified badge only meaningful when the seller is live (active plan).
        "badge": "verified" if (active and b.isVerified) else "pending",
        "enquiries": b.leadCount or 0,
        "responseSeconds": b.avgResponseSeconds,  # nullable → frontend formats
    }


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
        qs = (Business.objects.filter(filters)
              .select_related("user", "business_location")
              .prefetch_related(Prefetch(
                  "business_plan",
                  queryset=BusinessPlan.objects.filter(isActive=True).select_related("plan"),
                  to_attr="_active_plans"))
              .order_by("-id"))
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
