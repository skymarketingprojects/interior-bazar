from django.core.mail import send_mail
import httpx
import asyncio
from django.http import JsonResponse
from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES

from app_ib.Controllers.UrlGenrator.UrlGenrator import imageUrlGenrator

from app_ib.Utils.MyMethods import MY_METHODS

userCtrl = imageUrlGenrator()
# Create your views here.
@api_view(['GET'])
async def TestView(request):
    try:
        # file = request.data.get("lawyer_profile_image")
        # compress_image = await asyncio.gather(helpingMethos.MyImageCompression(type=COMPRESSSION_TYPE.LAWYER_PROFILE, image=file))
        # await MY_METHODS.printStatus(f'compress_image {compress_image[0]}')
        return JsonResponse({"result": 'success'})

    except Exception as e:
        await MY_METHODS.printStatus(e)
        return JsonResponse({"result": 'fail'})

@api_view(['POST'])
async def TestMailView(request):
    try:
        data = request.data
        email= data.get('email')
        subject=data.get('subject')
        message=data.get('message')
        link=data.get('link')
        await MY_METHODS.printStatus(f'email {email}')
        await MY_METHODS.printStatus(f'subject {subject}')
        await MY_METHODS.printStatus(f'message {message}')
        await MY_METHODS.printStatus(f'link {link}')


        send_mail(
            subject=f'{subject}',
            message=f'{message}\n forgot password: {link}',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[f'{email}'],
        )
        await MY_METHODS.printStatus('Email sent successfully!')
        return JsonResponse({"result": 'success'})
    except Exception as e:
        return JsonResponse({"result": 'error'})
        await MY_METHODS.printStatus(f'Email sending failed: {e}')

@api_view(['POST'])
async def generateUploadUrlView(request):
    try:
        fileName = request.data.get("fileName")
        fileType = request.data.get("fileType")
        ImageIntent = request.data.get("for")

        if not fileName or not fileType:
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.presigned_url_failed,
                data={}, code=RESPONSE_CODES.error
            )

        resp = await sync_to_async(userCtrl.GenerateImageUploadUrl)(fileName, fileType, ImageIntent)

        return ServerResponse(
            response=resp.response,
            message=resp.message,
            data=resp.data,
            code=resp.code
        )

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.presigned_url_failed,
            data={'error': str(e)},
            code=RESPONSE_CODES.error
        )