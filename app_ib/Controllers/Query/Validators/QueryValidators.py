# from typing import Optional
# from pydantic import BaseModel,validator
# # from pydantic.fields import 
# from django.db import models
# from app_ib.models import CustomUser
# from dateutil.parser import parse
# from datetime import date

# class leadQuerysData(BaseModel):
#     status: Optional[str]=None
#     priority: Optional[str]=None
#     leadFor: Optional[str]=None
#     fromDate: Optional[date]=None
#     toDate: Optional[date]=None

#     @validator("fromDate", "toDate", pre=True, always=True,allow_reuse=True)
#     def parse_dates(cls, value):
#         if value in (None, ""):
#             return None
#         if isinstance(value, date):
#             return value
#         return parse(value).date()

# class leadData(BaseModel):
#     id: Optional[int]=None
#     user: Optional[CustomUser]=None
#     name: Optional[str]=None
#     phone: Optional[int]=None
#     email: Optional[str]=None
#     interested: Optional[str]=None
#     query: Optional[str]=None
#     state: Optional[str]=None
#     country: Optional[str]=None
#     type: Optional[str]=None
#     itemId: Optional[int]=None
#     status: Optional[str]=None
#     tag: Optional[str]='default'
#     priority: Optional[str]=None
#     remark: Optional[str]=None

#     class Config:
#         arbitrary_types_allowed = True



from typing import Optional, Literal
from datetime import date
from pydantic import Field, EmailStr, validator
from dateutil.parser import parse

from app_ib.Utils.BaseValidator import BaseValidator
from app_ib.Utils.Names import NAMES

class LeadQueryFilterSchema(BaseValidator):
    status: Optional[str] = None
    priority: Optional[str] = None
    leadFor: Optional[Literal[
        'product',
        'service',
        'catalogue'
    ]] = None

    fromDate: Optional[date] = None
    toDate: Optional[date] = None

    @validator("fromDate", "toDate", pre=True, allow_reuse=True)
    def parse_dates(cls, v):
        if v in (None, ""):
            return None
        if isinstance(v, date):
            return v
        return parse(v).date()

class LeadQueryCreateSchema(BaseValidator):
    name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=7, max_length=15)
    email: Optional[EmailStr] = None

    interested: Optional[str] = None
    query: Optional[str] = None

    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

    type: Optional[Literal[
        'product',
        'service',
        'catalogue'
    ]] = None

    itemId: Optional[int] = Field(None, gt=0)

    @validator("phone", allow_reuse=True)
    def validate_phone(cls, v):
        if not v.isdigit():
            raise ValueError("phone must contain digits only")
        return v

class LeadQueryUpdateSchema(BaseValidator):
    id: int = Field(..., gt=0)

    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None

    interested: Optional[str] = None
    query: Optional[str] = None

    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

    status: Optional[str] = None
    tag: Optional[str] = None
    priority: Optional[str] = None
    remark: Optional[str] = None

    @validator("phone", allow_reuse=True)
    def validate_phone(cls, v):
        if v and not v.isdigit():
            raise ValueError("phone must contain digits only")
        return v

class LeadQueryStatusSchema(BaseValidator):
    id: int = Field(..., gt=0)
    status: str

class LeadQueryPrioritySchema(BaseValidator):
    id: int = Field(..., gt=0)
    priority: str

class LeadQueryRemarkSchema(BaseValidator):
    id: int = Field(..., gt=0)
    remark: str = Field(..., min_length=1)
