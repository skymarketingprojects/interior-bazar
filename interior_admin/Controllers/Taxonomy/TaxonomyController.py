from asgiref.sync import sync_to_async
from typing import Any, Dict, List, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.models import BusinessCategory, BusinessSegment, State
from interior_admin.Controllers.Audit.AuditController import append_audit
from .Validators.TaxonomyValidators import (
    CategoryCreateSchema, CategoryUpdateSchema,
    SegmentCreateSchema, SegmentUpdateSchema,
    StateCreateSchema, StateUpdateSchema,
)

MODULE = "cat-region"


def _cat(c: BusinessCategory) -> Dict[str, Any]:
    return {"id": c.id, "value": c.value, "label": c.lable, "trending": c.trending,
            "index": c.index, "isActive": c.isActive}


def _seg(s: BusinessSegment) -> Dict[str, Any]:
    return {"id": s.id, "value": s.value, "label": s.lable, "trending": s.trending,
            "isActive": s.isActive,
            "categoryIds": list(s.businessCategory.all().values_list("id", flat=True))}


def _state(s: State) -> Dict[str, Any]:
    return {"id": s.id, "name": s.name, "value": s.value,
            "countryId": s.country_id if hasattr(s, "country_id") else None}


class TaxonomyController:
    # ── read ──
    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def List(cls) -> Tuple[bool, Dict[str, Any]]:
        # Admin sees ALL taxonomy incl. hidden (isActive in payload); public reads
        # filter isActive=True elsewhere.
        cats = await sync_to_async(list)(BusinessCategory.objects.all().order_by("index"))
        segs = await sync_to_async(list)(
            BusinessSegment.objects.prefetch_related("businessCategory").all()[:300])
        states = await sync_to_async(list)(State.objects.all().order_by("name"))
        return True, {
            "categories": [_cat(c) for c in cats],
            "segments": await sync_to_async(lambda: [_seg(s) for s in segs])(),
            "states": [_state(s) for s in states],
        }

    # ── categories ──
    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def AddCategory(cls, payload: CategoryCreateSchema, actor=None) -> Tuple[bool, Dict[str, Any]]:
        if not payload.value or not payload.label:
            return False, {"message": "value and label are required"}
        if await BusinessCategory.objects.filter(value=payload.value).aexists():
            return False, {"message": "Category value already exists"}
        c = await BusinessCategory.objects.acreate(
            value=payload.value, lable=payload.label, trending=bool(payload.trending))
        await append_audit(actor=actor, action="category_added", module_key=MODULE, detail=f"value={payload.value}")
        return True, _cat(c)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def UpdateCategory(cls, categoryId: int, payload: CategoryUpdateSchema, actor=None) -> Tuple[bool, Dict[str, Any]]:
        c = await BusinessCategory.objects.filter(id=categoryId).afirst()
        if c is None:
            return False, {"message": "Category not found"}
        if payload.label is not None:
            c.lable = payload.label
        if payload.value is not None:
            c.value = payload.value
        if payload.trending is not None:
            c.trending = payload.trending
        if payload.index is not None:
            c.index = payload.index
        if payload.isActive is not None:
            c.isActive = payload.isActive
        await sync_to_async(c.save)()
        await append_audit(actor=actor, action="category_updated", module_key=MODULE, detail=f"category={c.id}")
        return True, _cat(c)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def DeleteCategory(cls, categoryId: int, actor=None) -> Tuple[bool, Dict[str, Any]]:
        # Soft delete: hide from public (isActive=False) rather than hard-delete,
        # which would orphan businesses linked via the M2M.
        c = await BusinessCategory.objects.filter(id=categoryId).afirst()
        if c is None:
            return False, {"message": "Category not found"}
        c.isActive = False
        await sync_to_async(c.save)()
        await append_audit(actor=actor, action="category_hidden", module_key=MODULE, detail=f"category={c.id}")
        return True, _cat(c)

    # ── segments (sub-categories) ──
    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def AddSegment(cls, payload: SegmentCreateSchema, actor=None) -> Tuple[bool, Dict[str, Any]]:
        if not payload.value or not payload.label:
            return False, {"message": "value and label are required"}
        s = await BusinessSegment.objects.acreate(
            value=payload.value, lable=payload.label, trending=bool(payload.trending))
        if payload.categoryIds:
            await sync_to_async(lambda: s.businessCategory.set(
                BusinessCategory.objects.filter(id__in=payload.categoryIds)))()
        await append_audit(actor=actor, action="segment_added", module_key=MODULE, detail=f"value={payload.value}")
        s = await BusinessSegment.objects.prefetch_related("businessCategory").aget(id=s.id)
        return True, await sync_to_async(_seg)(s)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def UpdateSegment(cls, segmentId: int, payload: SegmentUpdateSchema, actor=None) -> Tuple[bool, Dict[str, Any]]:
        s = await BusinessSegment.objects.filter(id=segmentId).afirst()
        if s is None:
            return False, {"message": "Segment not found"}
        if payload.value is not None:
            s.value = payload.value
        if payload.label is not None:
            s.lable = payload.label
        if payload.trending is not None:
            s.trending = payload.trending
        if payload.isActive is not None:
            s.isActive = payload.isActive
        await sync_to_async(s.save)()
        if payload.categoryIds is not None:
            await sync_to_async(lambda: s.businessCategory.set(
                BusinessCategory.objects.filter(id__in=payload.categoryIds)))()
        await append_audit(actor=actor, action="segment_updated", module_key=MODULE, detail=f"segment={s.id}")
        s = await BusinessSegment.objects.prefetch_related("businessCategory").aget(id=s.id)
        return True, await sync_to_async(_seg)(s)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def DeleteSegment(cls, segmentId: int, actor=None) -> Tuple[bool, Dict[str, Any]]:
        s = await BusinessSegment.objects.filter(id=segmentId).afirst()
        if s is None:
            return False, {"message": "Segment not found"}
        s.isActive = False
        await sync_to_async(s.save)()
        await append_audit(actor=actor, action="segment_hidden", module_key=MODULE, detail=f"segment={s.id}")
        s = await BusinessSegment.objects.prefetch_related("businessCategory").aget(id=s.id)
        return True, await sync_to_async(_seg)(s)

    # ── states ──
    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def AddState(cls, payload: StateCreateSchema, actor=None) -> Tuple[bool, Dict[str, Any]]:
        if not payload.name:
            return False, {"message": "name is required"}
        data = {"name": payload.name, "value": payload.value or payload.name}
        if payload.countryId:
            data["country_id"] = payload.countryId
        s = await State.objects.acreate(**data)
        await append_audit(actor=actor, action="state_added", module_key=MODULE, detail=f"name={payload.name}")
        return True, _state(s)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def UpdateState(cls, stateId: int, payload: StateUpdateSchema, actor=None) -> Tuple[bool, Dict[str, Any]]:
        s = await State.objects.filter(id=stateId).afirst()
        if s is None:
            return False, {"message": "State not found"}
        if payload.name is not None:
            s.name = payload.name
        if payload.value is not None:
            s.value = payload.value
        if payload.countryId is not None:
            s.country_id = payload.countryId
        await sync_to_async(s.save)()
        await append_audit(actor=actor, action="state_updated", module_key=MODULE, detail=f"state={s.id}")
        return True, _state(s)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def DeleteState(cls, stateId: int, actor=None) -> Tuple[bool, Dict[str, Any]]:
        s = await State.objects.filter(id=stateId).afirst()
        if s is None:
            return False, {"message": "State not found"}
        await sync_to_async(s.delete)()
        await append_audit(actor=actor, action="state_deleted", module_key=MODULE, detail=f"state={stateId}")
        return True, {"id": stateId, "deleted": True}


TAXONOMY_CONTROLLER = TaxonomyController()
