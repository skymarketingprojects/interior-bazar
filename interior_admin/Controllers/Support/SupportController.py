from asgiref.sync import sync_to_async
from django.db.models import Q
from django.utils import timezone
from typing import Any, Dict, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES

from app_ib.engine_models import SupportTicket
from .Validators.SupportValidators import SupportListFilters, ReplySchema


def _admin_ticket_dict(t: SupportTicket, full: bool = False) -> Dict[str, Any]:
    d = {
        "id": t.id,
        "subject": t.subject,
        "status": t.status,
        "user": t.user.username if t.user else None,
        "email": t.email,
        "createdAt": t.createdAt.isoformat() if t.createdAt else "",
        "lastReplyAt": t.lastReplyAt.isoformat() if t.lastReplyAt else "",
    }
    if full:
        d["message"] = t.message
        d["replies"] = t.replies or []
    return d


class SupportController:

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def ListTickets(cls, queryParams: SupportListFilters) -> Tuple[bool, Dict[str, Any]]:
        filters = Q()
        if queryParams.status:
            filters &= Q(status=queryParams.status)
        pageNo = max(1, queryParams.pageNo or 1)
        pageSize = min(100, max(1, queryParams.pageSize or 20))
        start = (pageNo - 1) * pageSize
        qs = SupportTicket.objects.filter(filters).select_related("user")
        total = await qs.acount()
        rows = await sync_to_async(list)(qs[start:start + pageSize])
        return True, {"tickets": [_admin_ticket_dict(t) for t in rows],
                      "total": total, "pageNo": pageNo, "pageSize": pageSize}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def GetTicket(cls, ticketId: int) -> Tuple[bool, Dict[str, Any]]:
        t = await SupportTicket.objects.select_related("user").filter(id=ticketId).afirst()
        if t is None:
            return False, {"message": "Ticket not found"}
        return True, _admin_ticket_dict(t, full=True)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def ReplyTicket(cls, ticketId: int, payload: ReplySchema, actor=None) -> Tuple[bool, Dict[str, Any]]:
        body = (payload.body or "").strip()
        if not body:
            return False, {"message": "Reply body is required"}
        t = await SupportTicket.objects.filter(id=ticketId).afirst()
        if t is None:
            return False, {"message": "Ticket not found"}
        now = timezone.now()
        reply = {
            "by": actor.username if getattr(actor, "is_authenticated", False) else "admin",
            "role": "admin",
            "body": body,
            "ts": now.isoformat(),
        }
        t.replies = (t.replies or []) + [reply]
        t.lastReplyAt = now
        if t.status == "open":
            t.status = "in_progress"
        await sync_to_async(t.save)()
        return True, _admin_ticket_dict(t, full=True)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def CloseTicket(cls, ticketId: int, actor=None) -> Tuple[bool, Dict[str, Any]]:
        t = await SupportTicket.objects.filter(id=ticketId).afirst()
        if t is None:
            return False, {"message": "Ticket not found"}
        t.status = "closed"
        await sync_to_async(t.save)()
        return True, {"id": t.id, "status": t.status}


SUPPORT_CONTROLLER = SupportController()
