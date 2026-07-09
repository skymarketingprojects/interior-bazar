from asgiref.sync import sync_to_async
from typing import Any, Dict, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES

from interior_admin.models import QualificationWeightConfig
from interior_admin.Controllers.Audit.AuditController import append_audit
from .Validators.WeightsValidators import WeightsSchema


# Fixed qualification signal weights + tier thresholds (task 15). Single source of
# truth for both the admin sliders and the lead scoring in CreateLeadQueryTask.
# Budget is deliberately NEVER a signal.
DEFAULT_WEIGHTS = {
    # signals
    "contact": 40, "genuineness": 20,
    "urgency_30d": 30, "urgency_90d": 20, "urgency_90plus": 10, "urgency_browsing": 0,
    "detail": 10,
    # tier score thresholds (0-100)
    "tier_A": 90, "tier_B": 75, "tier_C": 55, "tier_D": 35,
}


def merged_weights(stored: Dict[str, Any]) -> Dict[str, Any]:
    """Defaults overlaid with any stored overrides — so a missing/empty config
    still seeds the sliders and scoring."""
    return {**DEFAULT_WEIGHTS, **(stored or {})}


class WeightsController:

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Get(cls) -> Tuple[bool, Dict[str, Any]]:
        cfg, _ = await QualificationWeightConfig.objects.aget_or_create(id=1)
        return True, {"weights": merged_weights(cfg.weights), "updatedAt": cfg.updatedAt.isoformat() if cfg.updatedAt else ""}

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
