from asgiref.sync import sync_to_async
from django.db.models import Q
from typing import Any, Dict, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES

from interior_admin.models import ListingReport
from interior_admin.Controllers.Audit.AuditController import append_audit
from .Validators.ReportsValidators import ReportListFilters, ReportSubmitSchema, ReportResolveSchema

# 4-state moderation board: open → reviewing → actioned → dismissed (terminal).
ALLOWED_TRANSITIONS = {
    "open": {"reviewing", "actioned", "dismissed"},
    "reviewing": {"actioned", "dismissed"},
    "actioned": {"dismissed"},
    "dismissed": set(),  # terminal
}


def _r_dict(r: ListingReport) -> Dict[str, Any]:
    return {"id": r.id, "targetType": r.targetType, "targetId": r.targetId,
            "reason": r.reason, "status": r.status,
            "reporter": r.reporter.username if r.reporter else None,
            "reporterEmail": r.reporterEmail,
            "resolver": r.resolver.username if r.resolver else None,
            "createdAt": r.createdAt.isoformat() if r.createdAt else "",
            "updatedAt": r.updatedAt.isoformat() if r.updatedAt else ""}


class ReportsController:

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def List(cls, queryParams: ReportListFilters) -> Tuple[bool, Dict[str, Any]]:
        filters = Q()
        if queryParams.status:
            filters &= Q(status=queryParams.status)
        pageNo = max(1, queryParams.pageNo or 1)
        pageSize = min(100, max(1, queryParams.pageSize or 20))
        start = (pageNo - 1) * pageSize
        qs = ListingReport.objects.filter(filters).select_related("reporter", "resolver")
        total = await qs.acount()
        rows = await sync_to_async(list)(qs[start:start + pageSize])
        return True, {"reports": [_r_dict(r) for r in rows], "total": total,
                      "pageNo": pageNo, "pageSize": pageSize}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Submit(cls, payload: ReportSubmitSchema, reporter=None) -> Tuple[bool, Dict[str, Any]]:
        reason = (payload.reason or "").strip()
        if not reason:
            return False, {"message": "A reason is required"}
        r = await ListingReport.objects.acreate(
            reporter=reporter if getattr(reporter, "is_authenticated", False) else None,
            reporterEmail=payload.reporterEmail or '',
            targetType=payload.targetType or 'business', targetId=payload.targetId or '',
            reason=reason)
        return True, _r_dict(r)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Transition(cls, reportId: int, toStatus: str, actor=None) -> Tuple[bool, Dict[str, Any]]:
        """Advance a report along the moderation state machine. Rejects any edge
        not in ALLOWED_TRANSITIONS (e.g. a backward/skip jump)."""
        r = await ListingReport.objects.filter(id=reportId).afirst()
        if r is None:
            return False, {"message": "Report not found"}
        current = r.status or "open"
        if toStatus not in ALLOWED_TRANSITIONS.get(current, set()):
            return False, {"message": "Invalid transition"}
        r.status = toStatus
        r.resolver = actor if getattr(actor, "is_authenticated", False) else None
        await sync_to_async(r.save)()  # updatedAt auto_now
        await append_audit(actor=actor, action=f"report_{toStatus}", module_key="reports",
                           detail=f"report={r.id} {current}->{toStatus}")
        return True, _r_dict(r)


REPORTS_CONTROLLER = ReportsController()
