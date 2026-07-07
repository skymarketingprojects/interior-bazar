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
            "avatarUrl": t.avatarUrl,
            "updatedAt": t.updatedAt.isoformat() if t.updatedAt else ""}


class TestimonialsController:

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def List(cls) -> Tuple[bool, Dict[str, Any]]:
        rows = await sync_to_async(list)(Testimonial.objects.all())
        return True, {"testimonials": [_t_dict(t) for t in rows]}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def PublicList(cls) -> Tuple[bool, Dict[str, Any]]:
        rows = await sync_to_async(list)(Testimonial.objects.filter(status='active'))
        return True, {"testimonials": [_t_dict(t) for t in rows]}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Create(cls, payload: TestimonialCreateSchema) -> Tuple[bool, Dict[str, Any]]:
        t = await Testimonial.objects.acreate(
            author=payload.author, quote=payload.quote, role=payload.role or '',
            type=payload.type or 'text', featured=bool(payload.featured),
            status=payload.status or 'active', avatarUrl=payload.avatarUrl or '')
        return True, _t_dict(t)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Update(cls, testimonialId: int, payload: TestimonialUpdateSchema) -> Tuple[bool, Dict[str, Any]]:
        t = await Testimonial.objects.filter(id=testimonialId).afirst()
        if t is None:
            return False, {"message": "Testimonial not found"}
        for f in ("author", "quote", "role", "type", "featured", "status", "avatarUrl"):
            val = getattr(payload, f)
            if val is not None:
                setattr(t, f, val)
        await sync_to_async(t.save)()
        return True, _t_dict(t)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Delete(cls, testimonialId: int) -> Tuple[bool, Dict[str, Any]]:
        t = await Testimonial.objects.filter(id=testimonialId).afirst()
        if t is None:
            return False, {"message": "Testimonial not found"}
        await sync_to_async(t.delete)()
        return True, {"id": testimonialId, "deleted": True}


TESTIMONIALS_CONTROLLER = TestimonialsController()
