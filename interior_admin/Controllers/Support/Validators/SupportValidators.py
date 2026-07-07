from app_ib.Utils.BaseValidator import BaseValidator
from typing import Optional
from pydantic import Field


class SupportListFilters(BaseValidator):
    pageNo: Optional[int] = Field(default=1)
    pageSize: Optional[int] = Field(default=20)
    status: Optional[str] = Field(default=None)  # open|in_progress|resolved|closed


class ReplySchema(BaseValidator):
    body: str
