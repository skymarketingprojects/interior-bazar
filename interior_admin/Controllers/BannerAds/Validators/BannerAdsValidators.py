from app_ib.Utils.BaseValidator import BaseValidator
from typing import Optional
from pydantic import Field


class BannerAdListFilters(BaseValidator):
    status: Optional[str] = Field(default=None)  # AdStatus code, e.g. pending/approved/rejected
    pageNo: Optional[int] = Field(default=1)
    pageSize: Optional[int] = Field(default=20)


class RejectAdSchema(BaseValidator):
    reason: str
