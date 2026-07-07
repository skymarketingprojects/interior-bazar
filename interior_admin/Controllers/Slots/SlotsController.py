from asgiref.sync import sync_to_async
from typing import Any, Dict, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES

from interior_admin.models import SlotInventory
from interior_admin.Controllers.Audit.AuditController import append_audit
from .Validators.SlotsValidators import SlotOverrideSchema


def _slot_dict(s: SlotInventory) -> Dict[str, Any]:
    return {
        "id": s.id, "category": s.category, "region": s.region,
        "capacity": s.capacity, "priority": s.priority,
        "holderId": s.holder_id, "holder": s.holder.username if s.holder else None,
    }


class SlotsController:

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Grid(cls) -> Tuple[bool, Dict[str, Any]]:
        rows = await sync_to_async(list)(SlotInventory.objects.select_related("holder").all())
        return True, {"slots": [_slot_dict(s) for s in rows]}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Override(cls, slotId: int, payload: SlotOverrideSchema, actor=None) -> Tuple[bool, Dict[str, Any]]:
        s = await SlotInventory.objects.filter(id=slotId).afirst()
        if s is None:
            return False, {"message": "Slot not found"}
        if payload.capacity is not None:
            s.capacity = max(0, payload.capacity)
        if payload.priority is not None:
            s.priority = max(0, payload.priority)
        if payload.holderId is not None:
            s.holder_id = payload.holderId or None
        await sync_to_async(s.save)()
        await append_audit(actor=actor, action='slot_override', module_key='slots',
                           detail=f"{s.category}/{s.region} cap={s.capacity} priority={s.priority} holder={s.holder_id}")
        return True, _slot_dict(s)


SLOTS_CONTROLLER = SlotsController()
