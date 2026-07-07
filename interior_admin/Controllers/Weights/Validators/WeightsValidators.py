from app_ib.Utils.BaseValidator import BaseValidator
from typing import Optional, Dict
from pydantic import Field


class WeightsSchema(BaseValidator):
    weights: Dict[str, float] = Field(default_factory=dict)
    merge: Optional[bool] = Field(default=True)  # merge into existing vs replace
