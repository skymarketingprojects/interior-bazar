from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from datetime import timedelta
from asgiref.sync import sync_to_async, async_to_sync
from app_ib.models import UserProfile, BusinessPlan, LeadQuery, FunnelForm, PlanQuery, Business
from app_ib.Utils.MyMethods import MY_METHODS
from .Controllers.Publish import publishEmailToUser, WhatsappMessage, publishToUser
from .Controllers.Subscription import subscribeEmail, subscribeSMS
import asyncio
from interior_notification.signals import *

def run_in_background(coro):
    """Helper to fire and forget a coroutine."""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)
    except RuntimeError:
        # Fallback if no loop is running
        async_to_sync(lambda: coro)()

async def notify_signup_task(name, email, phone, country_code, is_business=False, business_name=None, bus_type=None):
    try:
        internationalPhone = await MY_METHODS.formatPhone(country_code=str(country_code), phone=str(phone))
        await sync_to_async(subscribeEmail)(email)
        await sync_to_async(subscribeSMS)(internationalPhone)
        
        sender_email = "hello@interiorbazzar.com"
        template = 'emails/welcomeMerchant.html' if is_business else 'emails/welcomeUser.html'
        context = {'name': name}
        if is_business:
            context.update({'businessType': bus_type, 'businessName': business_name})
            
        htmlBody = await sync_to_async(render_to_string)(template, context)
        await sync_to_async(publishEmailToUser)(senderEmail=sender_email, recipientEmail=email, subject="New signup", htmlBody=htmlBody)
    except Exception as e:
        await MY_METHODS.printStatus(f"Background Signup Notify Error: {e}")

@receiver(userSignupSignal)
def sendSignupNotification(sender, instance: UserProfile, created, **kwargs):
    if created and instance.user.type != "business":
        run_in_background(notify_signup_task(instance.name, instance.email, instance.phone, instance.countryCode))

@receiver(businessSignupSignal)
def sendSignupNotificationBusiness(sender, instance: Business, created, **kwargs):
    user = instance.user.user_profile
    run_in_background(notify_signup_task(
        user.name, user.email, user.phone, user.countryCode, 
        is_business=True, business_name=instance.businessName, bus_type=instance.businessType.lable
    ))

async def notify_plan_task(email, phone, country_code, context, text):
    try:
        internationalPhone = await MY_METHODS.formatPhone(country_code=str(country_code), phone=str(phone))
        htmlBody = await sync_to_async(render_to_string)('emails/planConfirmation.html', context)
        
        # Parallelize independent external calls
        await asyncio.gather(
            sync_to_async(publishEmailToUser)(senderEmail="hello@interiorbazzar.com", recipientEmail=email, subject="Plan Confirmation", htmlBody=htmlBody),
            sync_to_async(WhatsappMessage)(receiver_phone=internationalPhone, body_text=text),
            sync_to_async(publishToUser)(phone_number=internationalPhone, message=text)
        )
    except Exception as e:
        await MY_METHODS.printStatus(f"Background Plan Notify Error: {e}")

@receiver(planSignal)
def sendPlanNotification(sender, instance: BusinessPlan, **kwargs):
    try:
        if not instance.isActive: return
        business = instance.business
        user = business.user.user_profile
        
        context = {
            'businessName': business.businessName,
            'planName': instance.plan.title,
            'transectionId': instance.transactionId,
            'amount': instance.amount,
            'expireDate': instance.expireDate
        }
        text = f"transaction for plan {instance.plan.title} was successful with transaction id {instance.transactionId} and amount {instance.amount}"
        
        run_in_background(notify_plan_task(user.email, user.phone, user.countryCode, context, text))
    except: pass

@receiver(post_save, sender=FunnelForm)
def sendFunnelFormNotification(sender, instance: FunnelForm, created, **kwargs):
    if created:
        async def task():
            htmlBody = await sync_to_async(render_to_string)('emails/funnel.html', {'name': instance.name})
            await sync_to_async(publishEmailToUser)(senderEmail="hello@interiorbazzar.com", recipientEmail=instance.email, subject="Interior Bazzar form submission", htmlBody=htmlBody)
        run_in_background(task())

@receiver(post_save, sender=PlanQuery)
def sendPlanQueryNotification(sender, instance: PlanQuery, created, **kwargs):
    if created:
        async def task():
            htmlText = await sync_to_async(render_to_string)('emails/planQuery.html', {'plan': instance})
            await sync_to_async(publishEmailToUser)(senderEmail="hello@interiorbazzar.com", recipientEmail=instance.email, subject="Interior Bazzar plan", htmlBody=htmlText)
        run_in_background(task())

async def notify_lead_task(email, phone, countryCode, context, text, name, bus_name, lead_phone, lead_email):
    try:
        internationalPhone = await MY_METHODS.formatPhone(country_code=str(countryCode), phone=str(phone))
        await asyncio.gather(
            sync_to_async(publishEmailToUser)(senderEmail="hello@interiorbazzar.com", recipientEmail=email, subject="New Lead", textBody=text),
            sync_to_async(WhatsappMessage)(receiver_phone=internationalPhone, name=name, business_name=bus_name, phone=lead_phone, email=lead_email)
        )
    except Exception as e:
        await MY_METHODS.printStatus(f"Background Lead Notify Error: {e}")

@receiver(business_changed)
def leadqueryReceiver(sender, instance: LeadQuery, **kwargs):
    try:
        business = instance.business
        user = business.user.user_profile
        context = {"businessName": business.businessName, 'lead': instance}
        text = render_to_string('emails/leadQuery.txt', context)
        
        run_in_background(notify_lead_task(
            user.email, user.phone, user.countryCode, context, text, 
            instance.name, business.businessName, instance.phone, instance.email
        ))
    except: pass
