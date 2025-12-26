from asgiref.sync import sync_to_async
from app_ib.models import Subscription
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.Names import NAMES
class SUBSCRIPTION_TASKS:

    @classmethod
    async def CreateSubscriptionTask(self, data):
        try:
            # Creating a new subscription object
            subscription_ins = Subscription()
            subscription_ins.type = data[NAMES.TYPE]
            subscription_ins.title = data[NAMES.TITLE]
            subscription_ins.subtitle = data[NAMES.SUBTITLE]
            subscription_ins.services = data[NAMES.SERVICES]
            subscription_ins.duration = data[NAMES.DURATION]
            subscription_ins.tag = data[NAMES.TAG]
            subscription_ins.amount = data[NAMES.AMOUNT]
            subscription_ins.discountPercentage = data[NAMES.DISCOUNT_PERCENTAGE]
            subscription_ins.discountAmount = data[NAMES.DISCOUNT_AMOUNT]
            subscription_ins.payableAmount = data[NAMES.PAYABLE_AMOUNT]
            # subscription_ins.planPdfUrl = data.get(NAMES.COVER_IMAGE, None)
            subscription_ins.fallbackImageUrl = data.get(NAMES.FALLBACK_IMG, None)
            # subscription_ins.video = data.get(NAMES.VIDEO, None)
            subscription_ins.videoUrl = data.get(NAMES.VIDEO_URL, None)
            # subscription_ins.plan_pdf = data.get(NAMES.PLAN_PDF, None)
            subscription_ins.planPdfUrl = data.get(NAMES.PLAN_PDF_URL, None)
            subscription_ins.isActive = data[NAMES.IS_ACTIVE]
            
            await sync_to_async(subscription_ins.save)()
            return True
        
        except Exception as e:
            # await MY_METHODS.printStatus(f"Error in CreateSubscriptionTask {e}")
            return None
    
    @classmethod
    async def UpdateSubscriptionTask(self, subscription_ins:Subscription, data):
        try:
            subscription_ins.title = data[NAMES.TITLE]
            subscription_ins.subtitle = data[NAMES.SUBTITLE]
            subscription_ins.services = data[NAMES.SERVICES]
            subscription_ins.amount = data[NAMES.AMOUNT]
            subscription_ins.discountPercentage = data[NAMES.DISCOUNT_PERCENTAGE]
            subscription_ins.discountAmount = data[NAMES.DISCOUNT_AMOUNT]
            subscription_ins.payableAmount = data[NAMES.PAYABLE_AMOUNT]
            # subscription_ins.coverImage = data.get(NAMES.COVER_IMAGE, None)
            subscription_ins.fallbackImageUrl = data.get(NAMES.FALLBACK_IMG, None)
            # subscription_ins.videoUrl = data.get(NAMES.VIDEO, None)
            subscription_ins.videoUrl = data.get(NAMES.VIDEO_URL, None)
            # subscription_ins.plan_pdf = data.get(NAMES.PLAN_PDF, None)
            subscription_ins.planPdfUrl = data.get(NAMES.PLAN_PDF_URL, None)
            subscription_ins.isActive = data[NAMES.IS_ACTIVE]
            
            await sync_to_async(subscription_ins.save)()
            return True
        
        except Exception as e:
            # await MY_METHODS.printStatus(f"Error in UpdateSubscriptionTask {e}")
            return None

    @classmethod
    async def GetSubscriptionTask(self, subscription_ins:Subscription):
        try:
            # Convert subscription model into a dict format matching PlanType
            data = {
                NAMES.ID: subscription_ins.id,
                NAMES.TYPE: subscription_ins.type,
                NAMES.NAME: subscription_ins.title,  # Title as name
                NAMES.FEATURES: subscription_ins.services.split(NAMES.COMMA),  # Assuming services are comma-separated
                NAMES.PRICE:subscription_ins.payableAmount,  # Convert to a float for price
                NAMES.DESCRIPTION: subscription_ins.subtitle,
                NAMES.VIDEO: subscription_ins.videoUrl or NAMES.EMPTY,  # Fallback to empty string if not present
                NAMES.FALLBACK: subscription_ins.fallbackImageUrl or NAMES.EMPTY,
                NAMES.PLAN_PDF: subscription_ins.planPdfUrl or NAMES.EMPTY,
                NAMES.AVILABLE_DURATION:subscription_ins.availableDuration
            }
            return data
        
        except Exception as e:
            # await MY_METHODS.printStatus(f"Error in GetSubscriptionTask {e}")
            return None
    
    @classmethod
    async def GetSubscriptionsTask(self):
        try:
            query_data = []
            async for subscription in Subscription.objects.all():
                data = {
                    NAMES.ID: subscription.id,
                    NAMES.NAME: subscription.title,
                    NAMES.FEATURES: subscription.services.split(NAMES.COMMA),  # Assuming it's a comma-separated string
                    NAMES.PRICE: float(subscription.payableAmount),
                    NAMES.DESCRIPTION: subscription.subtitle,
                    NAMES.VIDEO: subscription.videoUrl or NAMES.EMPTY,
                    NAMES.FALLBACK: subscription.fallbackImageUrl or NAMES.EMPTY,
                    NAMES.PLAN_PDF: subscription.planPdfUrl or NAMES.EMPTY
                }
                query_data.append(data)

            return query_data
        
        except Exception as e:
            # await MY_METHODS.printStatus(f"Error in GetSubscriptionsTask: {e}")
            return None
