from app_ib.Utils.BaseValidator import BaseValidator
from typing import Optional, List
from pydantic import Field
from app_ib.Utils.Names import NAMES

class GMBLeadQueryFilters(BaseValidator):
    pageNo: Optional[int] = Field(default=1)
    pageSize: Optional[int] = Field(default=10)
    platform: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None)
    city: Optional[str] = Field(default=None)
    state: Optional[str] = Field(default=None)
    zip: Optional[str] = Field(default=None)
    has_website: Optional[bool] = Field(default=None)
    has_social: Optional[bool] = Field(default=None)
    min_rating: Optional[float] = Field(default=None)
    sort_by: Optional[str] = Field(default=NAMES.CREATED_AT)
    order: Optional[str] = Field(default="desc") # desc/asc

class GMBLeadUpdateSchema(BaseValidator):
    remark: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None)
    rankingRate: Optional[float] = Field(default=None)
    tier: Optional[str] = Field(default=None)
    category: Optional[str] = Field(default=None)
    state: Optional[str] = Field(default=None)

class GMBLeadCreateSchema(BaseValidator):
    businessName: str
    phone: str
    address: Optional[str] = Field(default=None)
    rating: Optional[str] = Field(default="0.0")
    website: Optional[str] = Field(default=None)
    map_link: Optional[str] = Field(default=None)
    social_links: Optional[List[str]] = Field(default=None)
    category: Optional[str] = Field(default=None)
    state: Optional[str] = Field(default=None)
    remark: Optional[str] = Field(default=None)
    platform: Optional[str] = Field(default="GMB")
