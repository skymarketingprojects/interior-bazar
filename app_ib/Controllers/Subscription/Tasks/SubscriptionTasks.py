from asgiref.sync import sync_to_async
from app_ib.models import Subscription

class SUBSCRIPTION_TASKS:

    @classmethod
    async def CreateSubscriptionTask(self, data):
        try:
            # Creating a new subscription object
            subscription_ins = Subscription()
            subscription_ins.type = data['type']
            subscription_ins.title = data['title']
            subscription_ins.subtitle = data['subtitle']
            subscription_ins.services = data['services']
            subscription_ins.duration = data['duration']
            subscription_ins.tag = data['tag']
            subscription_ins.amount = data['amount']
            subscription_ins.discount_percentage = data['discount_percentage']
            subscription_ins.discount_amount = data['discount_amount']
            subscription_ins.payable_amount = data['payable_amount']
            subscription_ins.cover_image = data.get('cover_image', None)
            subscription_ins.fallback_image_url = data.get('fallback_image_url', None)
            subscription_ins.video = data.get('video', None)
            subscription_ins.video_url = data.get('video_url', None)
            subscription_ins.plan_pdf = data.get('plan_pdf', None)
            subscription_ins.plan_pdf_url = data.get('plan_pdf_url', None)
            subscription_ins.is_active = data['is_active']
            
            await sync_to_async(subscription_ins.save)()
            return True
        
        except Exception as e:
            print(f"Error in CreateSubscriptionTask {e}")
            return None
    
    @classmethod
    async def UpdateSubscriptionTask(self, subscription_ins, data):
        try:
            subscription_ins.title = data['title']
            subscription_ins.subtitle = data['subtitle']
            subscription_ins.services = data['services']
            subscription_ins.amount = data['amount']
            subscription_ins.discount_percentage = data['discount_percentage']
            subscription_ins.discount_amount = data['discount_amount']
            subscription_ins.payable_amount = data['payable_amount']
            subscription_ins.cover_image = data.get('cover_image', None)
            subscription_ins.fallback_image_url = data.get('fallback_image_url', None)
            subscription_ins.video = data.get('video', None)
            subscription_ins.video_url = data.get('video_url', None)
            subscription_ins.plan_pdf = data.get('plan_pdf', None)
            subscription_ins.plan_pdf_url = data.get('plan_pdf_url', None)
            subscription_ins.is_active = data['is_active']
            
            await sync_to_async(subscription_ins.save)()
            return True
        
        except Exception as e:
            print(f"Error in UpdateSubscriptionTask {e}")
            return None

    @classmethod
    async def GetSubscriptionTask(self, subscription_ins):
        try:
            # Convert subscription model into a dict format matching PlanType
            data = {
                'id': subscription_ins.id,
                'name': subscription_ins.title,  # Title as name
                'features': subscription_ins.services.split(','),  # Assuming services are comma-separated
                'price':subscription_ins.payable_amount,  # Convert to a float for price
                'description': subscription_ins.subtitle,
                'video': subscription_ins.video_url or '',  # Fallback to empty string if not present
                'fallback': subscription_ins.fallback_image_url or '',
                'plan_pdf': subscription_ins.plan_pdf_url or ''
            }
            return data
        
        except Exception as e:
            print(f"Error in GetSubscriptionTask {e}")
            return None
    
    @classmethod
    async def GetSubscriptionsTask(self):
        try:
            query_data = []
            async for subscription in Subscription.objects.all():
                data = {
                    'id': subscription.id,
                    'name': subscription.title,
                    'features': subscription.services.split(','),  # Assuming it's a comma-separated string
                    'price': float(subscription.payable_amount),
                    'description': subscription.subtitle,
                    'video': subscription.video_url or '',
                    'fallback': subscription.fallback_image_url or '',
                    'plan_pdf': subscription.plan_pdf_url or ''
                }
                query_data.append(data)

            return query_data
        
        except Exception as e:
            print(f"Error in GetSubscriptionsTask: {e}")
            return None
