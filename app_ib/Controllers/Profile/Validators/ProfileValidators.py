from typing import Optional
from pydantic import EmailStr, Field, validator
from app_ib.Utils.BaseValidator import BaseValidator

class ProfileCreateOrUpdateSchema(BaseValidator):
    name: str = Field(..., min_length=2)
    email: Optional[EmailStr]
    phone: Optional[str]
    countryCode: Optional[str]
    profileImageUrl: Optional[str]

    @validator("phone", allow_reuse=True)
    def validate_phone(cls, v: str):
        if v and not v.isdigit():
            raise ValueError("Phone must contain digits only")
        return v