from typing import Optional
from pydantic import BaseModel,validator
# from pydantic.fields import 
from django.db import models
from app_ib.models import CustomUser
from dateutil.parser import parse
from datetime import date

class leadQuerysData(BaseModel):
    status: Optional[str]=None
    priority: Optional[str]=None
    leadFor: Optional[str]=None
    fromDate: Optional[date]=None
    toDate: Optional[date]=None

    @validator("fromDate", "toDate", pre=True, always=True,allow_reuse=True)
    def parse_dates(cls, value):
        if value in (None, ""):
            return None
        if isinstance(value, date):
            return value
        return parse(value).date()

class leadData(BaseModel):
    id: Optional[int]=None
    user: Optional[CustomUser]=None
    name: Optional[str]=None
    phone: Optional[int]=None
    email: Optional[str]=None
    interested: Optional[str]=None
    query: Optional[str]=None
    state: Optional[str]=None
    country: Optional[str]=None
    type: Optional[str]=None
    itemId: Optional[int]=None
    status: Optional[str]=None
    tag: Optional[str]='default'
    priority: Optional[str]=None
    remark: Optional[str]=None

    class Config:
        arbitrary_types_allowed = True



