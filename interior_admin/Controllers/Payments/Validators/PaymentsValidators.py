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
    paymentMethod: Optional[str] = Field(default=None)  # e.g. manual / gateway
    pageNo: Optional[int] = Field(default=1)
    pageSize: Optional[int] = Field(default=20)


class RejectPaymentSchema(BaseValidator):
    # Reject a submitted manual payment (task 11). Reason is audited.
    reason: Optional[str] = Field(default="")
