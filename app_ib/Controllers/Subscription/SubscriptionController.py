from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.models import Subscription, Business
from app_ib.Controllers.Subscription.Tasks.SubscriptionTasks import SUBSCRIPTION_TASKS
from django.core.cache import cache


class SUBSCRIPTION_CONTROLLER:

    @classmethod
    async def CreateSubscription(self, data):
        try:
            business_ins = None
            is_business_exist = await sync_to_async(Business.objects.filter(pk=data.buss_id).exists)()
            pass

            if is_business_exist:
                business_ins = await sync_to_async(Business.objects.get)(pk=data.buss_id)
                pass

                create_subscription_resp = await SUBSCRIPTION_TASKS.CreateSubscriptionTask(data=data)
                pass

                if create_subscription_resp:
                    # Invalidate cache on success
                    cache.delete("subscription_plans_list")
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
            pass

            if is_subscription_exist:
                subscription_ins = await sync_to_async(Subscription.objects.get)(id=data.id)
                pass

                update_subscription_resp = await SUBSCRIPTION_TASKS.UpdateSubscriptionTask(subscription_ins=subscription_ins, data=data)
                pass

                if update_subscription_resp:
                    # Invalidate cache on success
                    cache.delete("subscription_plans_list")
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
        cache_key = "subscription_plans_list"
        cached_data = cache.get(cache_key)
        if cached_data:
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.subscription_fetch_success,
                code=RESPONSE_CODES.success,
                data=cached_data
            )

        try:
            # Evaluate the queryset to a list before iterating
            subscription_qs = await sync_to_async(Subscription.objects.all)()
            subscription_ins = await sync_to_async(list)(subscription_qs)

            fetch_subscription_response = []
            for subscription in subscription_ins:
                subscription_response = await SUBSCRIPTION_TASKS.GetSubscriptionTask(subscription_ins=subscription)

                if subscription_response:
                    fetch_subscription_response.append(subscription_response)

            if fetch_subscription_response:
                # Cache for 24 hours
                cache.set(cache_key, fetch_subscription_response, 86400)
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
            pass

            fetch_subscription_response = []
            for subscription in subscription_ins:
                pass
                subscription_response = await SUBSCRIPTION_TASKS.GetSubscriptionTask(subscription_ins=subscription)

                if subscription_response:
                    fetch_subscription_response.append(subscription_response)
            pass

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

