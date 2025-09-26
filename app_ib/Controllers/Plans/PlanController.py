from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.models import PlanQuery
from app_ib.Controllers.Plans.Tasks.PlanTasks import PLAN_TASKS


class PLAN_CONTROLLER:
    @classmethod
    async def CreatePlan(self,payment_proof,data,user_ins):
        try:
            # Test Data
            plan_create_resp = await  PLAN_TASKS.CreatePlanTask(payment_proof=payment_proof, data=data, user_ins= user_ins)
            print(plan_create_resp)
            if plan_create_resp:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.plan_create_success,
                    code=RESPONSE_CODES.success,
                    data=plan_create_resp
                    )

            else:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.plan_create_error,
                    code=RESPONSE_CODES.error,
                    data={plan_create_resp})

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.plan_create_error,
                code=RESPONSE_CODES.error,
                data={
                    'error': str(e)
                })


    @classmethod
    async def VerifyPlan(self,data):
        try:
            is_plan_exist= await sync_to_async(PlanQuery.objects.filter(id=data.id).exists)()
            if(is_plan_exist):
                plan_ins=await sync_to_async(PlanQuery.objects.get)(id=data.id)
                #await MY_METHODS.printStatus(f'plan ins {plan_ins}')

                verify_plan_response = await  PLAN_TASKS.VerifyPlanTask(plan_ins=plan_ins,data=data)
                #await MY_METHODS.printStatus(f'verift plan resp {verify_plan_response}')

                if verify_plan_response:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.plan_verify_success,
                        code=RESPONSE_CODES.success,
                        data={"id":plan_ins.id})

                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.plan_verify_errror,
                        code=RESPONSE_CODES.error,
                        data={"id":plan_ins.id})
            else:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.plan_verify_errror,
                    code=RESPONSE_CODES.error,
                    data={})

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.plan_verify_errror,
                code=RESPONSE_CODES.error,
                data={
                    'error': str(e)
                })