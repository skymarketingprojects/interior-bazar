from app_ib.Utils.BaseValidator import BaseValidator
from typing import Optional, List
from pydantic import Field


class PlanUpdateSchema(BaseValidator):
    title: Optional[str] = Field(default=None)
    subtitle: Optional[str] = Field(default=None)
    amount: Optional[str] = Field(default=None)
    payableAmount: Optional[str] = Field(default=None)
    discountPercentage: Optional[str] = Field(default=None)
    duration: Optional[str] = Field(default=None)
    tag: Optional[str] = Field(default=None)
    features: Optional[List] = Field(default=None)  # [str] or [{text}] → [{text}]


class PlanCreateSchema(BaseValidator):
    planFamily: str  # required — free string so new families can be created
    entityType: Optional[str] = Field(default=None)
    title: Optional[str] = Field(default=None)
    subtitle: Optional[str] = Field(default=None)
    amount: Optional[str] = Field(default=None)
    payableAmount: Optional[str] = Field(default=None)
    discountPercentage: Optional[str] = Field(default=None)
    duration: Optional[str] = Field(default=None)
    tag: Optional[str] = Field(default=None)
    services: Optional[str] = Field(default=None)
    tier: Optional[int] = Field(default=None)
    features: Optional[List] = Field(default=None)


class PlanArchiveSchema(BaseValidator):
    isActive: bool
