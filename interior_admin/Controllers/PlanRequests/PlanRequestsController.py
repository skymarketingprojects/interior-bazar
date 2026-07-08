from asgiref.sync import sync_to_async
from django.db.models import Q
from typing import Any, Dict, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.models import PlanQuery
from interior_admin.Controllers.Audit.AuditController import append_audit


def _pq(p: PlanQuery) -> Dict[str, Any]:
    return {"id": p.id, "plan": p.plan, "name": p.name, "email": p.email, "phone": p.phone,
            "state": p.state, "stage": p.stage,
            "createdAt": p.timestamp.isoformat() if p.timestamp else ""}


class PlanRequestsController:
    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def List(cls, stage: str = None, pageNo: int = 1, pageSize: int = 20) -> Tuple[bool, Dict[str, Any]]:
        filters = Q()
        if stage:
            filters &= Q(stage=stage)
        pageNo = max(1, pageNo or 1); pageSize = min(100, max(1, pageSize or 20))
        start = (pageNo - 1) * pageSize
        qs = PlanQuery.objects.filter(filters).order_by("-id")
        total = await qs.acount()
        rows = await sync_to_async(list)(qs[start:start + pageSize])
        return True, {"requests": [_pq(p) for p in rows], "total": total, "pageNo": pageNo, "pageSize": pageSize}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def SetStage(cls, requestId: int, stage: str, actor=None) -> Tuple[bool, Dict[str, Any]]:
        p = await PlanQuery.objects.filter(id=requestId).afirst()
        if p is None:
            return False, {"message": "Plan request not found"}
        p.stage = stage
        await sync_to_async(p.save)()
        await append_audit(actor=actor, action=f"plan_request_{stage}", module_key="plan-requests", detail=f"request={p.id}")
        return True, _pq(p)


PLAN_REQUESTS_CONTROLLER = PlanRequestsController()
