from app_ib.Utils.BaseValidator import BaseValidator
from typing import Optional
from pydantic import Field


class PlanUpdateSchema(BaseValidator):
    title: Optional[str] = Field(default=None)
    subtitle: Optional[str] = Field(default=None)
    amount: Optional[str] = Field(default=None)
    payableAmount: Optional[str] = Field(default=None)
    discountPercentage: Optional[str] = Field(default=None)
    duration: Optional[str] = Field(default=None)
    tag: Optional[str] = Field(default=None)
