from rest_framework.permissions import IsAuthenticated, AllowAny
from adrf.views import APIView as AsyncAPIView
from adrf.decorators import api_view
from .Controllers.Publish import publishToTopic
from .Controllers.Subscription import subscribeEmail, subscribeSMS
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.models import Business
from django.http import HttpRequest

@api_view(['POST'])
async def SubscribeEmail(request: HttpRequest):
    try:
        email = request.data.get('email')
        if not email:
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                message="Email is required",
                code=RESPONSE_CODES.error,
                data={'error': "Email is required"}
            )
        response = subscribeEmail(email)
        return ServerResponse(
            response=RESPONSE_MESSAGES.success,
            message="Subscription successful",
            code=RESPONSE_CODES.success,
            data=response
        )
    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message="Subscription failed",
            code=RESPONSE_CODES.error,
            data={'error': str(e)}
        )
@api_view(['POST'])
async def SubscribeSMS(request: HttpRequest):
    try:
        phone_number = request.data.get('phone')
        if not phone_number:
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                message="Phone number is required",
                code=RESPONSE_CODES.error,
                data={'error': "Phone number is required"}
            )
        response = subscribeSMS(phone_number)
        return ServerResponse(
            response=RESPONSE_MESSAGES.success,
            message="Subscription successful",
            code=RESPONSE_CODES.success,
            data=response
        )
    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message="Subscription failed",
            code=RESPONSE_CODES.error,
            data={'error': str(e)}
        )
@api_view(['POST'])
async def PublishNotification(request: HttpRequest):
    try:
        message = request.data.get('message')
        subject = request.data.get('subject', 'Notification')
        if not message:
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                message="Message is required",
                code=RESPONSE_CODES.error,
                data={'error': "Message is required"}
            )
        response = publishToTopic(message, subject)
        return ServerResponse(
            response=RESPONSE_MESSAGES.success,
            message="Notification published successfully",
            code=RESPONSE_CODES.success,
            data=response
        )
    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message="Failed to publish notification",
            code=RESPONSE_CODES.error,
            data={'error': str(e)}
        )