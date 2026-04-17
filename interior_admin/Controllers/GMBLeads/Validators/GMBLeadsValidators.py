from app_ib.Utils.BaseValidator import BaseValidator
from typing import Optional, List
from pydantic import Field
from app_ib.Utils.Names import NAMES

class GMBLeadQueryFilters(BaseValidator):
    pageNo: Optional[int] = Field(default=1)
    pageSize: Optional[int] = Field(default=10)
    platform: Optional[str] = Field(default=None)
    city: Optional[str] = Field(default=None)
    zip: Optional[str] = Field(default=None)
    has_website: Optional[bool] = Field(default=None)
    has_social: Optional[bool] = Field(default=None)
    min_rating: Optional[float] = Field(default=None)
    sort_by: Optional[str] = Field(default=NAMES.RANKING_RATE)
    order: Optional[str] = Field(default="desc") # desc/asc
