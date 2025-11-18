
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from datetime import timedelta

from asgiref.sync import sync_to_async,async_to_sync
from app_ib.models import UserProfile,BusinessPlan,LeadQuery,FunnelForm,PlanQuery,Business
from app_ib.Utils.MyMethods import MY_METHODS

from .Controllers.Publish import publishEmailToUser,WhatsappMessage,publishToUser
from .Controllers.Subscription import subscribeEmail,subscribeSMS
import asyncio
from interior_notification.signals import *

@receiver(userSignupSignal)
# @receiver(post_save, sender=UserProfile)
def sendSignupNotification(sender, instance:UserProfile, created, **kwargs):
    try:
        async_to_sync(MY_METHODS.printStatus)("sendSignupNotification")
        email = instance.email
        phone = instance.phone
        countryCode = instance.countryCode
        internationalPhone= async_to_sync(MY_METHODS.formatPhone)(country_code=str(countryCode), phone=str(phone))
        if not email or not phone:
            return
        
        if created:
            name = instance.name

            sender_email = "hello@interiorbazzar.com"
            htmlBody= render_to_string('emails/welcomeUser.html',{'name':name})

            if instance.user.type == "business":
                return 0

            # publishEmailToUser(
            #     sender_email=sender_email,
            #     recipient_email=email,
            #     subject="New signup",
            #     html_body=htmlBody,
            #     text_body=text
            # )
            subscribeEmail(email)
            subscribeSMS(internationalPhone)
            publishEmailToUser(senderEmail=sender_email,recipientEmail=email,subject="New signup",htmlBody=htmlBody)

    except Exception as e:
        async_to_sync(MY_METHODS.printStatus)(f"Error in sendSignupNotification {e}")
        pass
@receiver(businessSignupSignal)
# @receiver(post_save, sender=BusinessProfile)
def sendSignupNotificationBusiness(sender, instance:Business, created, **kwargs):
    try:
        async_to_sync(MY_METHODS.printStatus)("sendSignupNotificationBusiness")
        user:UserProfile = instance.user.user_profile
        email = user.email
        phone = user.phone
        countryCode = user.countryCode
        internationalPhone= async_to_sync(MY_METHODS.formatPhone)(country_code=str(countryCode), phone=str(phone))
        if not email or not phone:
            return
        
        subscribeEmail(email)
        subscribeSMS(internationalPhone)
        
        busType=instance.businessType.lable
        businessName=instance.businessName
        name = user.name

        sender_email = "hello@interiorbazzar.com"
        htmlBody= render_to_string('emails/welcomeMerchant.html',{'name':name,'businessType':busType,'businessName':businessName})

        # publishEmailToUser(
        #     sender_email=sender_email,
        #     recipient_email=email,
        #     subject="New signup",
        #     html_body=htmlBody,
        #     text_body=text
        # )
        publishEmailToUser(senderEmail=sender_email,recipientEmail=email,subject="New signup",htmlBody=htmlBody)

    except Exception as e:
        async_to_sync(MY_METHODS.printStatus)(f"Error in sendSignupNotification {e}")
        pass

@receiver(planSignal)
# @receiver(post_save, sender=BusinessPlan)
def sendPlanNotification(sender, instance:BusinessPlan, **kwargs):
    try:
        timestamp = instance.timestamp
        now = timezone.now()
        if now - timestamp > timedelta(days=1):
            return
        
        if instance.isActive:
            business = instance.business
            if not business:
                return
            user:UserProfile = business.user.user_profile
            if not user:
                return
            
            
            email = user.email
            phone = user.phone
            countryCode = user.countryCode
            sender_email = "hello@interiorbazzar.com"
            amount = instance.amount
            planName = instance.plan.title
            transectionId = instance.transactionId
            businessName= instance.business.businessName
            amount=instance.amount
            expiryDate=instance.expireDate

            
            #creatig messages to send

            htmlBody= render_to_string('emails/planConfirmation.html',{
                'businessName':businessName,
                'planName':planName,
                'transectionId':transectionId,
                'amount':amount,
                'expireDate':expiryDate
                })
            text=f"transaction for plan {planName} was successful with transaction id {transectionId} and amount {amount}"

            internationalPhone=  async_to_sync(MY_METHODS.formatPhone)(country_code=str(countryCode), phone=str(phone))
            
            # calling notifiers
            publishEmailToUser(
                senderEmail=sender_email,
                recipientEmail=email,
                subject="New Lead",
                html_body=htmlBody,
            )
            WhatsappMessage(
                receiver_phone=internationalPhone,
                body_text=text
            )
            publishToUser(
                phone_number=internationalPhone,
                message=text
            )
            
    except Exception as e:
        async_to_sync(MY_METHODS.printStatus)(f"Error in sendPlanNotification {e}")
        pass

@receiver(post_save, sender=FunnelForm)
def sendFunnelFormNotification(sender, instance:FunnelForm, created, **kwargs):
    try:
        async_to_sync(MY_METHODS.printStatus)("sendFunnelFormNotification")
        email = instance.email
        subject= "Interior Bazzar form submission"
        text= render_to_string('emails/funnel.html',{'name':instance.name})
        # publishEmailToUser(
        #     sender_email="hello@interiorbazzar.com",
        #     recipient_email=email,
        #     subject=subject,
        #     text_body=text
        # )
        publishEmailToUser(
            senderEmail="hello@interiorbazzar.com",
            recipientEmail=email,
            subject=subject,
            htmlBody=text
        )
        # async_to_sync(MY_METHODS.send_email)(message=text,email=email,subject=subject)
    except Exception as e:
        async_to_sync(MY_METHODS.printStatus)(f"Error in sendFunnelFormNotification {e}")
        pass

@receiver(post_save, sender=PlanQuery)
def sendPlanQueryNotification(sender, instance:PlanQuery, created, **kwargs):
    try:
        if created:
            async_to_sync(MY_METHODS.printStatus)("sendPlanQueryNotification")
            email = instance.email
            async_to_sync(MY_METHODS.printStatus)(f"email: {email} instance: {instance}")
            
            subject= "Interior Bazzar plan"
            planName = instance.plan
            htmlText = render_to_string('emails/planQuery.html',{'plan':instance})
            publishEmailToUser(
                senderEmail="hello@interiorbazzar.com",
                recipientEmail=email,
                subject=subject,
                htmlBody=htmlText
            )
        return
    except Exception as e:
        async_to_sync(MY_METHODS.printStatus)(f"Error in sendFunnelFormNotification {e}")
        pass

@receiver(business_changed)
def leadqueryReceiver(sender, instance:LeadQuery, **kwargs):
    try:
        business = instance.business
        if not business:
            return
        user:UserProfile = business.user.user_profile
        if not user:
            return
        email = user.email
        phone = user.phone
        countryCode = user.countryCode
        sender_email = "hello@interiorbazzar.com"
        context={
            "businessName":business.businessName,
            'lead':instance,
        }


        htmlBody=f"Hello {user.name} <br> You have a new lead for your business."
        text = render_to_string('emails/leadQuery.txt',context)
        
        internationalPhone= async_to_sync(MY_METHODS.formatPhone)(country_code=str(countryCode), phone=str(phone))
        
        publishEmailToUser(
                senderEmail=sender_email,
                recipientEmail=email,
                subject="New Lead",
                textBody=text
                )
        WhatsappMessage(
                receiver_phone=internationalPhone,
                body_text=text
                )
        
    except Exception as e:
        async_to_sync(MY_METHODS.printStatus)(f"Error in leadqueryReceiver {e}")
        pass
 