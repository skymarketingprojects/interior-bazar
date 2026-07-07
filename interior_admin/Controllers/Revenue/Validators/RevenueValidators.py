from app_ib.Utils.BaseValidator import BaseValidator
from typing import Optional
from pydantic import Field


class ExpenseSchema(BaseValidator):
    label: str
    amount: float
    category: Optional[str] = Field(default='')
    incurredAt: Optional[str] = Field(default=None)  # ISO date
