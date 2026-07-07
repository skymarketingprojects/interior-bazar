from app_ib.Utils.BaseValidator import BaseValidator
from typing import Optional
from pydantic import Field


class RefundSchema(BaseValidator):
    amount: Optional[str] = Field(default=None)   # defaults to full txn amount if omitted
    reason: str
    reject: Optional[bool] = Field(default=False)  # true => record a refund rejection instead
