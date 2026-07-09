from asgiref.sync import sync_to_async
from typing import Any, Dict, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES

from interior_admin.models import Testimonial
from .Validators.TestimonialsValidators import TestimonialCreateSchema, TestimonialUpdateSchema


def _t_dict(t: Testimonial) -> Dict[str, Any]:
    return {"id": t.id, "author": t.author, "role": t.role, "quote": t.quote,
            "type": t.type, "featured": t.featured, "status": t.status,
            "avatarUrl": t.avatarUrl, "index": t.index, "videoUrl": t.videoUrl,
            "rating": t.rating, "businessName": t.businessName,
            "updatedAt": t.updatedAt.isoformat() if t.updatedAt else ""}


def _resequence():
    """Renumber every testimonial's index to a dense 1..n by current order.
    Sync helper (called via sync_to_async)."""
    rows = list(Testimonial.objects.all().order_by("index", "id"))
    for i, t in enumerate(rows, start=1):
        if t.index != i:
            t.index = i
            t.save(update_fields=["index"])


class TestimonialsController:

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def List(cls) -> Tuple[bool, Dict[str, Any]]:
        rows = await sync_to_async(list)(Testimonial.objects.all().order_by("index", "id"))
        return True, {"testimonials": [_t_dict(t) for t in rows]}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def PublicList(cls) -> Tuple[bool, Dict[str, Any]]:
        rows = await sync_to_async(list)(Testimonial.objects.filter(status='active').order_by("index", "id"))
        return True, {"testimonials": [_t_dict(t) for t in rows]}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Create(cls, payload: TestimonialCreateSchema) -> Tuple[bool, Dict[str, Any]]:
        # Append to the end of the current order.
        last = await Testimonial.objects.order_by("-index").afirst()
        next_index = (last.index + 1) if last else 1
        t = await Testimonial.objects.acreate(
            author=payload.author, quote=payload.quote, role=payload.role or '',
            type=payload.type or 'text', featured=bool(payload.featured),
            status=payload.status or 'active', avatarUrl=payload.avatarUrl or '',
            index=payload.index if payload.index is not None else next_index,
            videoUrl=payload.videoUrl or '', rating=payload.rating,
            businessName=payload.businessName or '')
        # If an explicit index was given, resequence so it slots cleanly.
        if payload.index is not None:
            await sync_to_async(_resequence)()
            t = await Testimonial.objects.aget(id=t.id)
        return True, _t_dict(t)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Update(cls, testimonialId: int, payload: TestimonialUpdateSchema) -> Tuple[bool, Dict[str, Any]]:
        t = await Testimonial.objects.filter(id=testimonialId).afirst()
        if t is None:
            return False, {"message": "Testimonial not found"}
        for f in ("author", "quote", "role", "type", "featured", "status", "avatarUrl",
                  "videoUrl", "rating", "businessName"):
            val = getattr(payload, f)
            if val is not None:
                setattr(t, f, val)
        await sync_to_async(t.save)()
        return True, _t_dict(t)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Reorder(cls, testimonialId: int, newIndex: int) -> Tuple[bool, Dict[str, Any]]:
        """Move a testimonial to newIndex (1-based) and renumber siblings densely."""
        t = await Testimonial.objects.filter(id=testimonialId).afirst()
        if t is None:
            return False, {"message": "Testimonial not found"}

        def _move():
            rows = list(Testimonial.objects.exclude(id=testimonialId).order_by("index", "id"))
            pos = max(0, min(len(rows), (newIndex or 1) - 1))
            rows.insert(pos, t)
            for i, row in enumerate(rows, start=1):
                if row.index != i:
                    row.index = i
                    row.save(update_fields=["index"])
        await sync_to_async(_move)()
        t = await Testimonial.objects.aget(id=testimonialId)
        return True, _t_dict(t)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Delete(cls, testimonialId: int) -> Tuple[bool, Dict[str, Any]]:
        t = await Testimonial.objects.filter(id=testimonialId).afirst()
        if t is None:
            return False, {"message": "Testimonial not found"}
        await sync_to_async(t.delete)()
        await sync_to_async(_resequence)()  # renumber remaining 1..n
        return True, {"id": testimonialId, "deleted": True}


TESTIMONIALS_CONTROLLER = TestimonialsController()
