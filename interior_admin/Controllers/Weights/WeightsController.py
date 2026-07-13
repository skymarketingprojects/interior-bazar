from asgiref.sync import sync_to_async
from typing import Any, Dict, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES

from interior_admin.models import QualificationWeightConfig
from interior_admin.Controllers.Audit.AuditController import append_audit
from .Validators.WeightsValidators import WeightsSchema, validate_weight_config


# Qualification signal *importances* + tier thresholds (task 33). The scorer takes
# a normalized weighted average, so these are relative weights (the effective % is
# weight/Σweights), NOT points that must sum to 100. Single source of truth for the
# admin sliders and the lead scoring in CreateLeadQueryTask. Budget is NEVER a signal.
DEFAULT_WEIGHTS = {
    # signals (relative importance)
    "contact": 40, "genuineness": 25, "detail": 15, "urgency": 20,
    # tier score thresholds (0-100), strictly descending
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
    async def Set(cls, payload: WeightsSchema, actor=None):
        """Validate + persist the weight config (task 33). Returns LocalResponse
        directly (not the tuple pattern) so a validation failure surfaces its own
        clear message to the admin instead of the generic error."""
        try:
            cfg, _ = await QualificationWeightConfig.objects.aget_or_create(id=1)
            if payload.merge:
                merged = merged_weights(cfg.weights)
                merged.update(payload.weights or {})
            else:
                # Replace, but keep defaults for any threshold/signal the UI omits so
                # validation always sees a complete config.
                merged = {**DEFAULT_WEIGHTS, **(payload.weights or {})}

            err = validate_weight_config(merged)
            if err:
                return LocalResponse(response=RESPONSE_MESSAGES.error, message=err,
                                     code=RESPONSE_CODES.validation_error, data={})

            cfg.weights = dict(merged)
            await sync_to_async(cfg.save)()
            await append_audit(actor=actor, action='weights_updated', module_key='weights',
                               detail=f"keys={list((payload.weights or {}).keys())} merge={payload.merge}")
            return LocalResponse(response=RESPONSE_MESSAGES.success, message="Weights saved.",
                                 code=RESPONSE_CODES.success, data={"weights": cfg.weights})
        except Exception as e:
            return LocalResponse(response=RESPONSE_MESSAGES.error, message=RESPONSE_MESSAGES.default_error,
                                 code=RESPONSE_CODES.error, data={})


WEIGHTS_CONTROLLER = WeightsController()
