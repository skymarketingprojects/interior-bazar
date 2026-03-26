
from app_ib.Utils.BaseValidator import BaseValidator
from typing import Optional, List, Literal
from datetime import datetime
from pydantic import Field, EmailStr, validator



class AdminLeadQueryFilters(BaseValidator):

    pageNo: Optional[int] = Field(default=1)
    pageSize: Optional[int] = Field(default=10)
    assigned: Optional[bool] = Field(default=None)
    timeFrom: Optional[datetime] = Field(default=None)
    timeTo: Optional[datetime] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)
    leadStatus: Optional[List[str]] = Field(default=None)
    stages: Optional[List[str]] = Field(default=None)
    status: Optional[List[str]] = Field(default=None)
    searchText: Optional[str] = Field(default=None)
    category: Optional[str] = Field(default=None)

    @validator("tags", "leadStatus", "stages", "status", pre=True)
    def ensure_list(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            # Split by comma if multiple values sent in one string (optional helper)
            return [x.strip() for x in v.split(",") if x.strip()]
        return v
class ClientLogSchema(BaseValidator):
    by: Literal['client', 'business']
    message: str = Field(..., min_length=1, max_length=1000)

class AdminLeadsCreateSchema(BaseValidator):
    name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=7, max_length=15)
    email: Optional[EmailStr] = None

    interested: Optional[str] = None
    query: Optional[str] = None
    leadStatus: Optional[str] = None
    stage: Optional[str] = None

    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    clientLogs: Optional[List[ClientLogSchema]] = None

    type: Optional[Literal[
        'product',
        'service',
        'catalogue'
    ]] = None

    itemId: Optional[int] = Field(None, gt=0)
    
    status: Optional[str] = None
    tag: Optional[str] = None
    priority: Optional[str] = None
    remark: Optional[str] = None

    @validator("phone", allow_reuse=True)
    def validate_phone(cls, v):
        if not v.isdigit():
            raise ValueError("phone must contain digits only")
        return v

class AdminLeadsUpdateSchema(BaseValidator):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, min_length=7, max_length=15)
    email: Optional[EmailStr] = None

    interested: Optional[str] = None
    query: Optional[str] = None
    leadStatus: Optional[str] = None
    stage: Optional[str] = None

    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

    type: Optional[Literal[
        'product',
        'service',
        'catalogue'
    ]] = None
    clientLogs: Optional[List[ClientLogSchema]] = None

    itemId: Optional[int] = Field(None, gt=0)

    status: Optional[str] = None
    tag: Optional[str] = None
    priority: Optional[str] = None
    remark: Optional[str] = None

    @validator("phone", allow_reuse=True)
    def validate_phone(cls, v):
        if not v.isdigit():
            raise ValueError("phone must contain digits only")
        return v
