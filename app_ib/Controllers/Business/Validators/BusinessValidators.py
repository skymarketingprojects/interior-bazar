
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.MyMethods import MY_METHODS


class BUSS_VALIDATOR:
    @classmethod
    async def _validate_business_name(self, business_name):
        try:
            error_msg = ''
            if business_name==None or business_name=='':
                error_msg = "At least one character required"
            if error_msg:
                return LocalResponse(
                    code=RESPONSE_CODES.error,
                    response=RESPONSE_MESSAGES.error,
                    message=error_msg,
                    data={})
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Business name is required",
                code=RESPONSE_CODES.error,
                data={
                    'error': error_msg
                })

    @classmethod
    async def _validate_business_phone(self, phone):
        try:
            error_msg = ''
            validate_phone=MY_METHODS._validate_phone(phone)
            if validate_phone==False:
                error_msg = "Invalid phone number"

            if error_msg:
                return LocalResponse(
                    code=RESPONSE_CODES.error,
                    response=RESPONSE_MESSAGES.error,
                    message=error_msg,
                    data={})

            return LocalResponse(
                code=RESPONSE_CODES.success,
                response=RESPONSE_MESSAGES.success,
                message="Phone number is valid",
                data={
                    'phone': phone
                })

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Phone number is required",
                code=RESPONSE_CODES.error,
                data={
                    'error': error_msg
                })


    @classmethod
    async def _validate_business_gst(self, gst):
        try:
            error_msg = ''
            validate_gst=MY_METHODS._validate_gst(gst)
            if validate_gst==False:
                error_msg = "Invalid GST number"

            if error_msg:
                return LocalResponse(
                    code=RESPONSE_CODES.error,
                    response=RESPONSE_MESSAGES.error,
                    message=error_msg,
                    data={})

            return LocalResponse(
                code=RESPONSE_CODES.success,
                response=RESPONSE_MESSAGES.success,
                message="GST number is valid",
                data={
                    'gst': gst
                })
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="GST number is required",
                code=RESPONSE_CODES.error,
                data={
                    'error': error_msg
                })

        
        
    @classmethod
    async def _validate_business_since(self, since):
        try:
            error_msg = ''
            
            if error_msg:
                return LocalResponse(
                    code=RESPONSE_CODES.error,
                    response=RESPONSE_MESSAGES.error,
                    message=error_msg,
                    data={})
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Business since is required",
                code=RESPONSE_CODES.error,
                data={
                    'error': error_msg
                })



    
