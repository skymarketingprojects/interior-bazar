from app_ib.Utils.BaseValidator import BaseValidator
from typing import Optional
from pydantic import Field


class ExpenseSchema(BaseValidator):
    label: str
    amount: float
    category: Optional[str] = Field(default='')
    kind: Optional[str] = Field(default='fixed')  # fixed | reinvestment
    incurredAt: Optional[str] = Field(default=None)  # ISO date


class AssumptionsSchema(BaseValidator):
    avgLifetimeMonths: Optional[int] = Field(default=None)
    grossMargin: Optional[float] = Field(default=None)       # 0..1
    revenueTarget: Optional[float] = Field(default=None)
    newCustomersThisMonth: Optional[int] = Field(default=None)
