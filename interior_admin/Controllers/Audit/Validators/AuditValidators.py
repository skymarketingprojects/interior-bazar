from app_ib.Utils.BaseValidator import BaseValidator
from typing import Optional
from pydantic import Field


class AuditQueryFilters(BaseValidator):
    pageNo: Optional[int] = Field(default=1)
    pageSize: Optional[int] = Field(default=20)
    module: Optional[str] = Field(default=None)   # filter by moduleKey
    role: Optional[str] = Field(default=None)
    dateFrom: Optional[str] = Field(default=None)  # ISO date, inclusive
    dateTo: Optional[str] = Field(default=None)    # ISO date, inclusive
