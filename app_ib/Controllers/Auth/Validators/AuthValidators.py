# from app_ib.Utils.LocalResponse import LocalResponse
# from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
# from app_ib.Utils.ResponseCodes import RESPONSE_CODES
# from app_ib.Utils.ResponseMessages import VALIDATION_MESSAGES



# class AUTH_VALIDATOR: 
#     @classmethod
#     async def _validate_password(self,password):
#         msg = ""
#         try:
#             if len(password) < 8:
#                 msg = VALIDATION_MESSAGES.password_length
#                 raise ValueError(VALIDATION_MESSAGES.password_length)
#             if not any(char.isdigit() for char in password):
#                 msg = VALIDATION_MESSAGES.password_must_contain_digit
#                 raise ValueError(VALIDATION_MESSAGES.password_must_contain_digit)
#             if not any(char.isalpha() for char in password):
#                 msg = VALIDATION_MESSAGES.password_must_contain_letter
#                 raise ValueError(VALIDATION_MESSAGES.password_must_contain_letter)
           
#             return LocalResponse(
#                 code=RESPONSE_CODES.success,
#                 response=RESPONSE_MESSAGES.success,
#                 message=RESPONSE_MESSAGES.default_success,
#                 data={}
#             )
#         except ValueError as e:
#             return LocalResponse(
#                 code=RESPONSE_CODES.error,
#                 response=RESPONSE_MESSAGES.error,
#                 data=str(e),
#                 message=msg
#             )

from pydantic import Field, validator
from app_ib.Utils.BaseValidator import BaseValidator

class SignupValidator(BaseValidator):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)
    type: str

    @validator("password")
    def validate_password(cls, v):
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter")
        return v


class LoginValidator(BaseValidator):
    username: str
    password: str


class ForgotPasswordValidator(BaseValidator):
    username: str


class ChangePasswordValidator(BaseValidator):
    password: str
    confirm_password: str
    hash: str

    @validator("confirm_password")
    def passwords_match(cls, v, values):
        if "password" in values and v != values["password"]:
            raise ValueError("Passwords do not match")
        return v


class ResetPasswordValidator(BaseValidator):
    old_password: str
    password: str
