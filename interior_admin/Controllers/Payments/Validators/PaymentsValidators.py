from app_ib.Utils.BaseValidator import BaseValidator
from typing import Optional
from pydantic import Field


class RefundSchema(BaseValidator):
    amount: Optional[str] = Field(default=None)   # defaults to full txn amount if omitted
    reason: str
    reject: Optional[bool] = Field(default=False)  # true => record a refund rejection instead


class PaymentListFilters(BaseValidator):
    status: Optional[str] = Field(default=None)     # orderStatus, e.g. PAID / REFUNDED
    refunded: Optional[bool] = Field(default=None)  # only refunded rows
    pageNo: Optional[int] = Field(default=1)
    pageSize: Optional[int] = Field(default=20)
