from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Controllers.Business.Tasks.BusinessTasks import BUSS_TASK
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.models import Business


class BUSS_CONTROLLER:
    @classmethod
    async def CreateBusiness(self, user_ins, data):
        try:
            # Check if business already exist
            is_business_exist = await sync_to_async(Business.objects.filter(user=user_ins).exists)()
            if is_business_exist:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.business_already_exist,
                    code=RESPONSE_CODES.error,
                    data={})
            # Create business
            business_ins = await BUSS_TASK.CreateBusinessTask(user_ins=user_ins, data=data)
            if business_ins is None:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.business_register_error,
                    code=RESPONSE_CODES.error,
                    data={})

            return LocalResponse(
                code=RESPONSE_CODES.success,
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.business_register_success,
                data={})
                
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_register_error,
                code=RESPONSE_CODES.error,
                data={
                    'error': str(e)
                })

    @classmethod
    async def UpdateeBusiness(self, user_ins, data):
        try:
            # Check if business already exist
            is_business_exist = await sync_to_async(Business.objects.filter(user=user_ins).exists)()
            business_data = None

            if is_business_exist:
                business_instance = await sync_to_async(Business.objects.get)(user=user_ins)
                #await MY_METHODS.printStatus(f'business instance {business_instance}')
                
                business_ins = await BUSS_TASK.UpdateBusinessTask(business_ins=business_instance, data=data)
                if business_ins is None:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.business_update_error,
                        code=RESPONSE_CODES.error,
                        data={})
                business_data = await BUSS_TASK.GetBusinessInfo(id=business_instance.id)
                return LocalResponse(
                    code=RESPONSE_CODES.success,
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.business_update_success,
                    data=business_data)

            return LocalResponse(
                code=RESPONSE_CODES.success,
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.business_register_success,
                data=business_data)

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_register_error,
                code=RESPONSE_CODES.error,
                data={
                    'error': str(e)
                })

    @classmethod
    async def GetBusinessById(self,id):
        try:
            # Check if business already exist
            is_business_exist = await sync_to_async(Business.objects.filter(pk=id).exists)()

            if is_business_exist:
                business_data = await BUSS_TASK.GetBusinessInfo(id=id)
                #await MY_METHODS.printStatus(f'business data {business_data}')

                if business_data is not None:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.business_fetch_success,
                        code=RESPONSE_CODES.success,
                        data=business_data)
                
                return LocalResponse(
                    code=RESPONSE_CODES.success,
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.business_fetch_error,
                    data={})

            return LocalResponse(
                code=RESPONSE_CODES.success,
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.business_fetch_success,
                data={})

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_fetch_error,
                code=RESPONSE_CODES.error,
                data={
                    'error': str(e)
                })