
from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import sync_to_async,async_to_sync
from app_ib.models import UserProfile,BusinessPlan,LeadQuery,FunnelForm,PlanQuery
from app_ib.Utils.MyMethods import MY_METHODS

from .Controllers.Publish import publishEmailToUser,WhatsappMessage,publishToUser
from .Controllers.Subscription import subscribeEmail,subscribeSMS
import asyncio
from interior_notification.signals import business_changed

@receiver(post_save, sender=UserProfile)
def sendSignupNotification(sender, instance:UserProfile, created, **kwargs):
    try:
        print("sendSignupNotification")
        email = instance.email
        phone = instance.phone
        countryCode = instance.countryCode
        internationalPhone= async_to_sync(MY_METHODS.formatPhone)(country_code=str(countryCode), phone=str(phone))
        if not email or not phone:
            return
        
        subscribeEmail(email)
        subscribeSMS(internationalPhone)
        if created:

            sender_email = "hello@interiorbazzar.com"
            htmlBody=f"Hello {email} <br> Your account has been created successfully.<br> Your phone number is {phone}"
            text = f"Hello {email} Your account has been created successfully. Your phone number is {phone}"
            whatsappTxt = f"Hello {phone} Your account has been created successfully. Your email is {email}"

            # publishEmailToUser(
            #     sender_email=sender_email,
            #     recipient_email=email,
            #     subject="New signup",
            #     html_body=htmlBody,
            #     text_body=text
            # )
            publishEmailToUser(senderEmail=sender_email,recipientEmail=email,subject="New signup",body=text)
            WhatsappMessage(
                receiver_phone=internationalPhone,
                body_text=whatsappTxt
            )

    except Exception as e:
        print(f"Error in sendSignupNotification {e}")
        pass

@receiver(post_save, sender=BusinessPlan)
def sendPlanNotification(sender, instance:BusinessPlan, created, **kwargs):
    try:
        if instance.isActive:
            business = instance.business
            if not business:
                return
            user = business.user.user_profile
            if not user:
                return
            
            
            email = user.email
            phone = user.phone
            countryCode = user.countryCode
            sender_email = "hello@interiorbazzar.com"
            amount = instance.amount
            planName = instance.plan.title
            transectionId = instance.transactionId
            
            #creatig messages to send

            htmlBody=f"Thank You {user.name} for choosing our plan. <br> Your plan is {planName} <br> Your transaction id is {transectionId} <br> Your amount is {amount}"
            text = f" Thank You {user.name} for choosing our plan. Your plan is {planName} Your transaction id is {transectionId} Your amount is {amount}"
            whatsappTxt = f" Thank You {user.name} for choosing our plan. Your plan is {planName} Your transaction id is {transectionId} Your amount is {amount}"
            internationalPhone=  async_to_sync(MY_METHODS.formatPhone)(country_code=str(countryCode), phone=str(phone))
            
            # calling notifiers
            publishEmailToUser(
                senderEmail=sender_email,
                recipientEmail=email,
                subject="New Lead",
                html_body=htmlBody,
                text_body=text
            )
            WhatsappMessage(
                receiver_phone=internationalPhone,
                body_text=whatsappTxt
            )
            publishToUser(
                phone_number=internationalPhone,
                message=text
            )
            
    except Exception as e:
        pass

@receiver(post_save, sender=FunnelForm)
def sendFunnelFormNotification(sender, instance:FunnelForm, created, **kwargs):
    try:
        print("sendFunnelFormNotification")
        email = instance.email
        subject= "Interior Bazzar form submission"
        text= f"Name: {instance.name} \n Email: {instance.email} \n Your form has been submitted successfully.\n Our team will get back to you soon."
        # publishEmailToUser(
        #     sender_email="hello@interiorbazzar.com",
        #     recipient_email=email,
        #     subject=subject,
        #     text_body=text
        # )
        # publishEmailToUser(
        #     senderEmail="hello@interiorbazzar.com",
        #     recipientEmail=email,
        #     subject=subject,
        #     body=text
        # )
        async_to_sync(MY_METHODS.send_email)(message=text,email=email,subject=subject)
    except Exception as e:
        print(e)
        pass

@receiver(post_save, sender=PlanQuery)
def sendPlanQueryNotification(sender, instance:PlanQuery, created, **kwargs):
    try:
        email = instance.email
        subject= "Interior Bazzar plan"
        planName = instance.plan.title
        htmlText = f"Name: {instance.name} <br> Email: {instance.email} <br> Your form for plan <strong>{planName}</strong> has been submitted successfully.<br> Our team will get back to you soon."
        publishEmailToUser(
            sender_email="hello@interiorbazzar.com",
            recipient_email=email,
            subject=subject,
            html_body=htmlText
        )
    except Exception as e:
        print(e)
        pass

@receiver(business_changed)
def leadqueryReceiver(sender, instance:LeadQuery, **kwargs):
    try:
        business = instance.business
        if not business:
            return
        user = business.user.user_profile
        if not user:
            return
        email = user.email
        phone = user.phone
        countryCode = user.countryCode
        sender_email = "hello@interiorbazzar.com"
        htmlBody=f"Hello {user.name} <br> You have a new lead for your business."
        text = f"Hello {user.name} \n You have a new lead for your business."
        whatsappTxt = f"Hello {user.name} \n You have a new lead for your business."
        internationalPhone= MY_METHODS.formatPhone(country_code=str(countryCode), phone=str(phone))
        tasks = [
            asyncio.create_task(publishEmailToUser(
                sender_email=sender_email,
                recipient_email=email,
                subject="New Lead",
                html_body=htmlBody,
                text_body=text
                )),
            asyncio.create_task(WhatsappMessage(
                receiver_phone=internationalPhone,
                body_text=whatsappTxt
                ))
        ]
        asyncio.gather(*tasks)
    except Exception as e:
        pass
 