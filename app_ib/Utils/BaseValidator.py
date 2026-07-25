import os

import email_validator
from pydantic import BaseModel, Extra

# email-validator 2.x rejects RFC 2606 special-use TLDs, so every `EmailStr` field
# (profile, leads, admin leads) 400s on the QA seed accounts (*@ibazzar.test).
# Outside prod, drop only 'test' from that list — localhost/invalid/onion and all
# malformed-address checks stay on. Every validator module imports BaseValidator,
# so patching here covers all EmailStr callers at once.
if os.environ.get('MODE', 'prod') != 'prod':
    email_validator.SPECIAL_USE_DOMAIN_NAMES = [
        d for d in email_validator.SPECIAL_USE_DOMAIN_NAMES if d != 'test'
    ]


class BaseValidator(BaseModel):
    class Config:
        extra = Extra.ignore
        orm_mode = True

class LocalResponse(BaseValidator):
    response: bool
    code: int
    message: str
    data: dict
