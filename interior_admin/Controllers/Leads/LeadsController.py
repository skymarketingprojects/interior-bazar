from asgiref.sync import sync_to_async
from django.db.models import Q
from typing import Any, Dict, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.models import LeadQuery
from interior_admin.Controllers.Audit.AuditController import append_audit


def _lead(l: LeadQuery) -> Dict[str, Any]:
    return {
        "id": l.id, "name": l.name, "phone": l.phone, "email": l.email,
        "interested": l.interested, "query": l.query, "city": l.city, "state": l.state,
        "country": l.country, "category": l.category, "stage": l.stage, "tag": l.tag,
        "status": l.status, "leadStatus": l.leadStatus,
        "tier": l.tier, "score": l.score, "remark": l.remark,
        "timeline": l.timeline,
        "business": l.business.businessName if l.business_id else None,
    }


class LeadsController:
    """Backs both routing (held enquiries) and quarantine (genuineness) modules —
    both operate on LeadQuery, differing by the status filter/action."""

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def List(cls, status: str = None, tier: str = None, excludeQuarantine: bool = False,
                   pageNo: int = 1, pageSize: int = 20) -> Tuple[bool, Dict[str, Any]]:
        filters = Q()
        if status:
            filters &= Q(status__icontains=status)
        if tier:
            filters &= Q(tier=tier)
        # Routing passes excludeQuarantine=True so quarantined/spam leads don't leak
        # into the routing queue (fixes the bug where status=None returned ALL leads).
        # Also drop already-assigned leads: assigning sets business (AssignLeadQueryTask)
        # but no status change, so without this an assigned lead stays in the queue.
        if excludeQuarantine:
            filters &= ~Q(status__icontains="quarantine") & ~Q(status__icontains="spam")
            filters &= Q(business__isnull=True)
        pageNo = max(1, pageNo or 1); pageSize = min(100, max(1, pageSize or 20))
        start = (pageNo - 1) * pageSize
        qs = LeadQuery.objects.filter(filters).select_related("business").order_by("-id")
        total = await qs.acount()
        rows = await sync_to_async(list)(qs[start:start + pageSize])
        return True, {"leads": [_lead(l) for l in rows], "total": total, "pageNo": pageNo, "pageSize": pageSize}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def SetStatus(cls, leadId: int, status: str, moduleKey: str, actor=None) -> Tuple[bool, Dict[str, Any]]:
        l = await LeadQuery.objects.filter(id=leadId).afirst()
        if l is None:
            return False, {"message": "Lead not found"}
        l.status = status
        await sync_to_async(l.save)()
        await append_audit(actor=actor, action=f"lead_{status}", module_key=moduleKey, detail=f"lead={l.id}")
        return True, _lead(l)


LEADS_CONTROLLER = LeadsController()
