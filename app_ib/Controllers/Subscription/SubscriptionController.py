from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.models import Subscription, Business
from app_ib.Controllers.Subscription.Tasks.SubscriptionTasks import SUBSCRIPTION_TASKS


class SUBSCRIPTION_CONTROLLER:

    @classmethod
    async def CreateSubscription(self, data):
        try:
            business_ins = None
            is_business_exist = await sync_to_async(Business.objects.filter(pk=data.buss_id).exists)()
            # await MY_METHODS.printStatus(f'is_business_exist {is_business_exist}')

            if is_business_exist:
                business_ins = await sync_to_async(Business.objects.get)(pk=data.buss_id)
                # await MY_METHODS.printStatus(f'business_ins {business_ins}')

                create_subscription_resp = await SUBSCRIPTION_TASKS.CreateSubscriptionTask(data=data)
                # await MY_METHODS.printStatus(f'create subscription resp {create_subscription_resp}')

                if create_subscription_resp:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.subscription_create_success,
                        code=RESPONSE_CODES.success,
                        data=create_subscription_resp
                    )
                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.subscription_create_error,
                        code=RESPONSE_CODES.error,
                        data={}
                    )

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.subscription_create_error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )

    @classmethod
    async def UpdateSubscription(self, data):
        try:
            subscription_ins = None
            is_subscription_exist = await sync_to_async(Subscription.objects.filter(id=data.id).exists)()
            # await MY_METHODS.printStatus(f'is_subscription_exist {is_subscription_exist}')

            if is_subscription_exist:
                subscription_ins = await sync_to_async(Subscription.objects.get)(id=data.id)
                # await MY_METHODS.printStatus(f'subscription_ins {subscription_ins}')

                update_subscription_resp = await SUBSCRIPTION_TASKS.UpdateSubscriptionTask(subscription_ins=subscription_ins, data=data)
                # await MY_METHODS.printStatus(f'update subscription resp {update_subscription_resp}')

                if update_subscription_resp:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.subscription_update_success,
                        code=RESPONSE_CODES.success,
                        data=update_subscription_resp
                    )
                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.subscription_update_error,
                        code=RESPONSE_CODES.error,
                        data={}
                    )

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.subscription_update_error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )

    @classmethod
    async def GetSubscription(self):
        try:
            subscription_ins = await sync_to_async(Subscription.objects.all)()
            # await MY_METHODS.printStatus(f'subscription_ins {subscription_ins}')

            fetch_subscription_response = []
            for subscription in subscription_ins:
                # await MY_METHODS.printStatus(f'subscription {subscription}')
                subscription_response = await SUBSCRIPTION_TASKS.GetSubscriptionTask(subscription_ins=subscription)

                if subscription_response:
                    fetch_subscription_response.append(subscription_response)
            # await MY_METHODS.printStatus(f'fetch subscription resp {fetch_subscription_response}')

            if fetch_subscription_response:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.subscription_fetch_success,
                    code=RESPONSE_CODES.success,
                    data=fetch_subscription_response
                )
            else:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.subscription_fetch_error,
                    code=RESPONSE_CODES.error,
                    data={}
                )

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.subscription_fetch_error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )

    @classmethod
    async def GetSubscriptionById(self,id):
        try:
            subscription_ins = await sync_to_async(Subscription.objects.filter)(id=id)
            # await MY_METHODS.printStatus(f'subscription_ins {subscription_ins}')

            fetch_subscription_response = []
            for subscription in subscription_ins:
                # await MY_METHODS.printStatus(f'subscription {subscription}')
                subscription_response = await SUBSCRIPTION_TASKS.GetSubscriptionTask(subscription_ins=subscription)

                if subscription_response:
                    fetch_subscription_response.append(subscription_response)
            # await MY_METHODS.printStatus(f'fetch subscription resp {fetch_subscription_response}')

            if fetch_subscription_response:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.subscription_fetch_success,
                    code=RESPONSE_CODES.success,
                    data=fetch_subscription_response
                )
            else:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.subscription_fetch_error,
                    code=RESPONSE_CODES.error,
                    data={}
                )

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.subscription_fetch_error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )

