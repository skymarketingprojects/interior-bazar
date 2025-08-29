from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.ResponseMessages import VALIDATION_MESSAGES



class AUTH_VALIDATOR: 
    @classmethod
    async def _validate_password(self,password):
        try:
            msg = ""
           
            if len(password) < 8:
                msg = VALIDATION_MESSAGES.password_length
                raise ValueError(VALIDATION_MESSAGES.password_length)
            if not any(char.isdigit() for char in password):
                msg = VALIDATION_MESSAGES.password_must_contain_digit
                raise ValueError(VALIDATION_MESSAGES.password_must_contain_digit)
            if not any(char.isalpha() for char in password):
                msg = VALIDATION_MESSAGES.password_must_contain_letter
                raise ValueError(VALIDATION_MESSAGES.password_must_contain_letter)
           
            return LocalResponse(
                code=RESPONSE_CODES.success,
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.default_success,
                data={}
            )
        except ValueError as e:
            return LocalResponse(
                code=RESPONSE_CODES.error,
                response=RESPONSE_MESSAGES.error,
                data=str(e),
                message=msg
            )

