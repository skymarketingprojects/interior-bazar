from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.models import Quate
from app_ib.Controllers.PlanQuate.Tasks.Tasks import PLAN_QUATE_TASKS


class PLAN_QUATE_CONTROLLER:
    @classmethod
    async def CreateQuate(self,data):
        try:
            # Test Data
            print(f'name: {data.phone}')
            print(f'name: {data.interested}')
            print(f'name: {data.email}')
            print(f'name: {data.note}')

            quate_create_resp_data = await  PLAN_QUATE_TASKS.CreateQuateTask(data=data)
            print(f'create query resp {quate_create_resp_data}')

            if quate_create_resp_data:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.Quate_generate_success,
                    code=RESPONSE_CODES.success,
                    data={
                        'query_id':quate_create_resp_data
                    })

            else:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.quate_generate_error,
                    code=RESPONSE_CODES.error,
                    data={})

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.quate_generate_error,
                code=RESPONSE_CODES.error,
                data={
                    'error': str(e)
                })

    @classmethod
    async def VerifyQuate(self,data):
        try:
            # Test Data
            # print(f'name: {data.phone}')
            # print(f'name: {data.interested}')
            # print(f'name: {data.email}')
            # print(f'name: {data.note}')

            is_quate_exist= await sync_to_async(Quate.objects.filter(id=data.id).exists)()
            if(is_quate_exist):
                quate_ins=await sync_to_async(Quate.objects.get)(id=data.id)
                print(f'quate ins {quate_ins}')

                verify_quate_response = await  PLAN_QUATE_TASKS.VerifyQuateTask(quate_ins=quate_ins, data=data)
                print(f'veruft quate resp {verify_quate_response}')

                if verify_quate_response:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.Quate_verify_success,
                        code=RESPONSE_CODES.success,
                        data={})

                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.Quate_verify_errror,
                        code=RESPONSE_CODES.error,
                        data={})
            else:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.Quate_verify_errror,
                    code=RESPONSE_CODES.error,
                    data={})

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.Quate_verify_errror,
                code=RESPONSE_CODES.error,
                data={
                    'error': str(e)
                })