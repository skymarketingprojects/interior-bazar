from typing import Optional
from pydantic import Field, validator,AnyUrl
from app_ib.Utils.BaseValidator import BaseValidator


# ----------------------------------
# Nested ID Schema (State / Country)
# ----------------------------------
class IDOnlySchema(BaseValidator):
    id: int = Field(..., gt=0)


# ----------------------------------
# Create / Update Client Location
# ----------------------------------
class ClientLocationCreateOrUpdateSchema(BaseValidator):
    pinCode: str = Field(..., min_length=4, max_length=10)
    city: str = Field(..., min_length=1, max_length=100)

    state: IDOnlySchema
    country: IDOnlySchema

    locationLink: Optional[AnyUrl] = None

    @validator("pinCode", allow_reuse=True)
    def validate_pincode(cls, v):
        if not v.isdigit():
            raise ValueError("pinCode must contain digits only")
        return v


# ----------------------------------
# Client Location Response Schema
# ----------------------------------
class ClientLocationResponseSchema(BaseValidator):
    id: int
    pinCode: str
    city: str
    state: str
    country: str
    locationLink: Optional[str] = None
