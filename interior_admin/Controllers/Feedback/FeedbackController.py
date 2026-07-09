from asgiref.sync import sync_to_async
from django.db.models import Q
from typing import Any, Dict, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.models import Feedback
from interior_admin.Controllers.Audit.AuditController import append_audit


def _fb(f: Feedback) -> Dict[str, Any]:
    return {"id": f.id, "contact": f.contact, "feedback": f.feedback,
            "status": f.status or "new",  # blank submissions are triaged as 'new'
            "user": f.user.username if f.user_id else None,
            "createdAt": f.timestamp.isoformat() if f.timestamp else ""}


class FeedbackController:
    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def List(cls, status: str = None, pageNo: int = 1, pageSize: int = 20) -> Tuple[bool, Dict[str, Any]]:
        filters = Q()
        if status:
            # Submissions come in with an empty status; treat those as 'new'.
            if status == "new":
                filters &= Q(status="") | Q(status__iexact="new")
            else:
                filters &= Q(status__icontains=status)
        pageNo = max(1, pageNo or 1); pageSize = min(100, max(1, pageSize or 20))
        start = (pageNo - 1) * pageSize
        qs = Feedback.objects.filter(filters).select_related("user").order_by("-id")
        total = await qs.acount()
        rows = await sync_to_async(list)(qs[start:start + pageSize])
        return True, {"feedback": [_fb(f) for f in rows], "total": total, "pageNo": pageNo, "pageSize": pageSize}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def SetStatus(cls, feedbackId: int, status: str, actor=None) -> Tuple[bool, Dict[str, Any]]:
        f = await Feedback.objects.filter(id=feedbackId).afirst()
        if f is None:
            return False, {"message": "Feedback not found"}
        f.status = status
        await sync_to_async(f.save)()
        await append_audit(actor=actor, action=f"feedback_{status}", module_key="feedback", detail=f"feedback={f.id}")
        return True, _fb(f)


FEEDBACK_CONTROLLER = FeedbackController()
