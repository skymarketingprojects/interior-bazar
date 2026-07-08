from asgiref.sync import sync_to_async
from typing import Any, Dict, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.models import BusinessCategory, BusinessSegment, State
from interior_admin.Controllers.Audit.AuditController import append_audit


class TaxonomyController:
    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def List(cls) -> Tuple[bool, Dict[str, Any]]:
        cats = await sync_to_async(list)(BusinessCategory.objects.all().order_by("index"))
        segs = await sync_to_async(list)(BusinessSegment.objects.all()[:200])
        states = await sync_to_async(list)(State.objects.all().order_by("name"))
        return True, {
            "categories": [{"id": c.id, "value": c.value, "label": c.lable, "trending": c.trending, "index": c.index} for c in cats],
            "segments": [{"id": s.id, "value": getattr(s, "value", None), "label": getattr(s, "lable", None)} for s in segs],
            "states": [{"id": s.id, "name": s.name, "value": s.value} for s in states],
        }

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def AddCategory(cls, value: str, label: str, actor=None) -> Tuple[bool, Dict[str, Any]]:
        if not value or not label:
            return False, {"message": "value and label are required"}
        if await BusinessCategory.objects.filter(value=value).aexists():
            return False, {"message": "Category value already exists"}
        c = await BusinessCategory.objects.acreate(value=value, lable=label)
        await append_audit(actor=actor, action="category_added", module_key="cat-region", detail=f"value={value}")
        return True, {"id": c.id, "value": c.value, "label": c.lable}


TAXONOMY_CONTROLLER = TaxonomyController()
