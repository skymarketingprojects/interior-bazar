from typing import Optional
from pydantic import Field
from app_ib.Utils.BaseValidator import BaseValidator

class AccessCreateSchema(BaseValidator):
    Name: str = Field(..., min_length=1, max_length=255)
    HasAccess: Optional[bool] = False

class AccessUpdateSchema(BaseValidator):
    Id: int = Field(..., gt=0)
    Name: Optional[str] = None
    HasAccess: Optional[bool] = None
