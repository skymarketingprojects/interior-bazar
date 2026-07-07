from asgiref.sync import sync_to_async
from typing import Any, Dict, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES

from interior_admin.models import QualificationWeightConfig
from interior_admin.Controllers.Audit.AuditController import append_audit
from .Validators.WeightsValidators import WeightsSchema


class WeightsController:

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Get(cls) -> Tuple[bool, Dict[str, Any]]:
        cfg, _ = await QualificationWeightConfig.objects.aget_or_create(id=1)
        return True, {"weights": cfg.weights or {}, "updatedAt": cfg.updatedAt.isoformat() if cfg.updatedAt else ""}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Set(cls, payload: WeightsSchema, actor=None) -> Tuple[bool, Dict[str, Any]]:
        cfg, _ = await QualificationWeightConfig.objects.aget_or_create(id=1)
        if payload.merge:
            merged = dict(cfg.weights or {})
            merged.update(payload.weights or {})
            cfg.weights = merged
        else:
            cfg.weights = dict(payload.weights or {})
        await sync_to_async(cfg.save)()
        await append_audit(actor=actor, action='weights_updated', module_key='weights',
                           detail=f"keys={list((payload.weights or {}).keys())} merge={payload.merge}")
        return True, {"weights": cfg.weights}


WEIGHTS_CONTROLLER = WeightsController()
