from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.models import PlanQuery,BusinessPlan,CustomUser,Subscription
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
                    NAMES.ERROR: str(e)
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
                        data={NAMES.ID:plan_ins.id})

                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.plan_verify_errror,
                        code=RESPONSE_CODES.error,
                        data={NAMES.ID:plan_ins.id})
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
                    NAMES.ERROR: str(e)
                })

    @classmethod
    async def CreateBusinessPlan(self,planId,userId,transectionId):
        try:
            user = await sync_to_async(CustomUser.objects.get)(id=userId)
            businessId = user.user_business.id
            plan = await sync_to_async(Subscription.objects.get)(id=planId)
            data = await PLAN_TASKS.CreateBusinessPlan(plan=plan,businessId=businessId,transectionId=transectionId)
            if data:
                await MY_METHODS.printStatus(f'Business plan created successfully for user {userId} with plan {planId}')
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.business_plan_create_success,
                    code=RESPONSE_CODES.success,
                    data=data
                    )

            else:
                await MY_METHODS.printStatus(f'Failed to create business plan for user {userId} with plan {planId}')
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.business_plan_create_error,
                    code=RESPONSE_CODES.error,
                    data={})

        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in CreateBusinessPlan: {e}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_plan_create_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })
    @classmethod
    async def ActivateBusinessPlan(self,transectionId):
        try:
            is_plan_exist= await sync_to_async(BusinessPlan.objects.filter(transactionId=transectionId).exists)()
            if(is_plan_exist):
                planIns=await sync_to_async(BusinessPlan.objects.get)(transactionId=transectionId)
                activate_plan_response = await  PLAN_TASKS.ActivateBusinessPlan(planIns)
                if activate_plan_response:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.business_plan_activate_success,
                        code=RESPONSE_CODES.success,
                        data={NAMES.ID:planIns.id})

                else:
                    #await MY_METHODS.printStatus(f'Failed to activate business plan for transaction id {transectionId}')
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.business_plan_activate_error,
                        code=RESPONSE_CODES.error,
                        data={NAMES.ID:planIns.id})
            else:
                #await MY_METHODS.printStatus(f'Business plan does not exist for transaction id {transectionId}')
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.business_plan_activate_error,
                    code=RESPONSE_CODES.error,
                    data={})

        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in ActivateBusinessPlan: {e}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_plan_activate_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })
        
    @classmethod
    async def GetBusinessPlan(self,user):
        try:
            business = user.user_business
            plans = business.business_plan.all()
            plansData= {}
            for plan in plans:
                if plan.isActive == False:
                    continue
                data = await PLAN_TASKS.GetBusinessPlanData(businessPlan=plan)
                if data:
                    plansData=data
                if plan.isActive == True:
                    break

            if plansData:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.business_plan_fetch_success,
                    code=RESPONSE_CODES.success,
                    data=plansData
                    )

            else:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.business_plan_fetch_error,
                    code=RESPONSE_CODES.error,
                    data={})

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_plan_fetch_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })