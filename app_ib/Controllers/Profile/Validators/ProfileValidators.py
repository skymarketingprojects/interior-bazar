from typing import Optional
from pydantic import EmailStr, Field, validator
from app_ib.Utils.BaseValidator import BaseValidator

class ProfileCreateOrUpdateSchema(BaseValidator):
    name: str = Field(..., min_length=2)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    countryCode: Optional[str] = None
    profileImageUrl: Optional[str] = None

    @validator("email", pre=True, allow_reuse=True)
    def blank_email_to_none(cls, v):
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        return v

    @validator("phone", allow_reuse=True)
    def validate_phone(cls, v: str):
        if v and not v.isdigit():
            raise ValueError("Phone must contain digits only")
        return v