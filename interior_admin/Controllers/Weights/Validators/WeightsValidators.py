from app_ib.Utils.BaseValidator import BaseValidator
from typing import Optional, Dict
from pydantic import Field


# The 4 qualification signals + tier thresholds the config must describe (task 33).
SIGNAL_KEYS = ("contact", "genuineness", "detail", "urgency")
THRESHOLD_KEYS = ("tier_A", "tier_B", "tier_C", "tier_D")


class WeightsSchema(BaseValidator):
    weights: Dict[str, float] = Field(default_factory=dict)
    merge: Optional[bool] = Field(default=True)  # merge into existing vs replace


def validate_weight_config(weights: Dict[str, float]) -> Optional[str]:
    """Reject an invalid MERGED weight config with a clear admin-facing message,
    else return None (task 33). Rules: every value >= 0; at least one signal
    weight > 0; tier thresholds strictly descending A > B > C > D. Runs on the
    merged result so merge=true can't sneak in an invalid combined state."""
    weights = weights or {}
    for key, val in weights.items():
        try:
            if float(val) < 0:
                return f"'{key}' must be zero or a positive number."
        except (TypeError, ValueError):
            return f"'{key}' must be a number."

    signal_sum = sum(float(weights.get(k, 0) or 0) for k in SIGNAL_KEYS)
    if signal_sum <= 0:
        return "At least one signal weight must be greater than zero."

    a, b, c, d = (float(weights.get(k, 0) or 0) for k in THRESHOLD_KEYS)
    if not (a > b > c > d):
        return "Tier thresholds must be strictly descending: A > B > C > D."
    return None
