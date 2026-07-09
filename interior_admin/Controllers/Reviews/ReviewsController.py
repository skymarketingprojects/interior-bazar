from asgiref.sync import sync_to_async
from typing import Any, Dict, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.engine_models import Review, ShopQuestion
from interior_admin.Controllers.Audit.AuditController import append_audit


def _review(r: Review) -> Dict[str, Any]:
    author = r.reviewer.username if r.reviewer_id else None
    return {
        "id": r.id, "rating": r.rating, "title": r.title, "body": r.body,
        "reviewer": author, "author": author,
        "business": r.business.businessName if r.business_id else None,
        "date": r.timestamp.isoformat() if r.timestamp else None,
        "isApproved": r.isApproved, "isDeleted": r.isDeleted, "replyText": r.replyText,
    }


def _question(q: ShopQuestion) -> Dict[str, Any]:
    return {
        "id": q.id,
        "business": q.shop.name if q.shop_id else None,
        "question": q.question, "answer": q.answer, "askedBy": q.askedBy,
        "date": q.timestamp.isoformat() if q.timestamp else None,
        "isActive": q.isActive,
    }


class ReviewsController:
    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def List(cls, pageNo: int = 1, pageSize: int = 20) -> Tuple[bool, Dict[str, Any]]:
        pageNo = max(1, pageNo or 1); pageSize = min(100, max(1, pageSize or 20))
        start = (pageNo - 1) * pageSize
        # Latest first (timestamp, not id).
        qs = Review.objects.filter(isDeleted=False).select_related("reviewer", "business").order_by("-timestamp")
        total = await qs.acount()
        rows = await sync_to_async(list)(qs[start:start + pageSize])
        return True, {"reviews": [_review(r) for r in rows], "total": total, "pageNo": pageNo, "pageSize": pageSize}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def QA(cls, pageNo: int = 1, pageSize: int = 20) -> Tuple[bool, Dict[str, Any]]:
        """Real per-shop Q&A (ShopQuestion) shown on the frontend. Read-only here +
        a hide toggle; sellers answer. Not the static help QNA model."""
        pageNo = max(1, pageNo or 1); pageSize = min(100, max(1, pageSize or 20))
        start = (pageNo - 1) * pageSize
        qs = ShopQuestion.objects.select_related("shop").order_by("-timestamp")
        total = await qs.acount()
        rows = await sync_to_async(list)(qs[start:start + pageSize])
        return True, {"questions": [_question(q) for q in rows], "total": total, "pageNo": pageNo, "pageSize": pageSize}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def QAHide(cls, questionId: int, actor=None) -> Tuple[bool, Dict[str, Any]]:
        q = await ShopQuestion.objects.select_related("shop").filter(id=questionId).afirst()
        if q is None:
            return False, {"message": "Question not found"}
        q.isActive = not q.isActive
        await sync_to_async(q.save)()
        await append_audit(actor=actor, action=("qa_shown" if q.isActive else "qa_hidden"),
                           module_key="reviews", detail=f"question={q.id}")
        return True, _question(q)

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
