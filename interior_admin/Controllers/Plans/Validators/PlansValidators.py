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
    badge: Optional[str] = Field(default=None)      # "Most popular" ribbon on the public card
    badgeIcon: Optional[str] = Field(default=None)  # tabler icon name
    tier: Optional[int] = Field(default=None)       # ordering + upgrade rank
    features: Optional[List] = Field(default=None)  # [str] or [{text}] → [{text}]


class PlanCycleCreateSchema(BaseValidator):
    """One PlanBillingCycle. price/oldPrice accepted as strings (Decimal money)."""
    durationMonths: int
    price: str
    oldPrice: Optional[str] = Field(default=None)
    badgeLabel: Optional[str] = Field(default=None)
    isActive: Optional[bool] = Field(default=None)


class PlanCycleUpdateSchema(BaseValidator):
    durationMonths: Optional[int] = Field(default=None)
    price: Optional[str] = Field(default=None)
    oldPrice: Optional[str] = Field(default=None)
    badgeLabel: Optional[str] = Field(default=None)
    isActive: Optional[bool] = Field(default=None)


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
    badge: Optional[str] = Field(default=None)
    badgeIcon: Optional[str] = Field(default=None)
    services: Optional[str] = Field(default=None)
    tier: Optional[int] = Field(default=None)
    features: Optional[List] = Field(default=None)
    cycles: Optional[List[PlanCycleCreateSchema]] = Field(default=None)  # create plan + cycles in one call


class PlanArchiveSchema(BaseValidator):
    isActive: bool
