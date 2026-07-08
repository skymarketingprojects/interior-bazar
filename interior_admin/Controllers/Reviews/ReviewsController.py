from asgiref.sync import sync_to_async
from typing import Any, Dict, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.engine_models import Review
from interior_admin.Controllers.Audit.AuditController import append_audit


def _review(r: Review) -> Dict[str, Any]:
    return {
        "id": r.id, "rating": r.rating, "title": r.title, "body": r.body,
        "reviewer": r.reviewer.username if r.reviewer_id else None,
        "business": r.business.businessName if r.business_id else None,
        "isApproved": r.isApproved, "isDeleted": r.isDeleted, "replyText": r.replyText,
    }


class ReviewsController:
    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def List(cls, pageNo: int = 1, pageSize: int = 20) -> Tuple[bool, Dict[str, Any]]:
        pageNo = max(1, pageNo or 1); pageSize = min(100, max(1, pageSize or 20))
        start = (pageNo - 1) * pageSize
        qs = Review.objects.filter(isDeleted=False).select_related("reviewer", "business").order_by("-id")
        total = await qs.acount()
        rows = await sync_to_async(list)(qs[start:start + pageSize])
        return True, {"reviews": [_review(r) for r in rows], "total": total, "pageNo": pageNo, "pageSize": pageSize}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Hide(cls, reviewId: int, actor=None) -> Tuple[bool, Dict[str, Any]]:
        r = await Review.objects.filter(id=reviewId).afirst()
        if r is None:
            return False, {"message": "Review not found"}
        r.isApproved = not r.isApproved
        await sync_to_async(r.save)()
        await append_audit(actor=actor, action=("review_shown" if r.isApproved else "review_hidden"),
                           module_key="reviews", detail=f"review={r.id}")
        return True, _review(r)


REVIEWS_CONTROLLER = ReviewsController()
