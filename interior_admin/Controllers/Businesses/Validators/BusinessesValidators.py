from app_ib.Utils.BaseValidator import BaseValidator
from typing import Optional
from pydantic import Field


class BusinessListFilters(BaseValidator):
    search: Optional[str] = Field(default=None)
    pageNo: Optional[int] = Field(default=1)
    pageSize: Optional[int] = Field(default=20)
