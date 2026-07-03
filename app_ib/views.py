from django.core.mail import send_mail
import httpx
import asyncio
from django.core.cache import cache
from django.http import JsonResponse
from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from django.views.decorators.csrf import csrf_exempt
from app_ib.Controllers.UrlGenrator.UrlGenrator import imageUrlGenrator
from .models import OurClients,ReelSection
from app_ib.Utils.MyMethods import MY_METHODS
from rest_framework.serializers import ModelSerializer

userCtrl = imageUrlGenrator()

# ponytail: hardcoded temp list, remove this whole view when the real routing feature lands
_phone_numbers = ['9315663588', '8920898168']
_PHONE_COUNTER_KEY = 'round_robin_phone_counter'

def _get_next_phone():
	# cache.incr is atomic in redis, safe across multiple uvicorn workers/processes
	try:
		count = cache.incr(_PHONE_COUNTER_KEY)
	except ValueError:
		cache.set(_PHONE_COUNTER_KEY, 1)
		count = 1
	return _phone_numbers[(count - 1) % len(_phone_numbers)]
# Create your views here.
@api_view(['GET'])
async def TestView(request):
    try:
        # file = request.data.get("lawyer_profile_image")
        # compress_image = await asyncio.gather(helpingMethods.MyImageCompression(type=COMPRESSSION_TYPE.LAWYER_PROFILE, image=file))
        pass
        return JsonResponse({"result": 'success'})

    except Exception as e:
        pass
        return JsonResponse({"result": 'fail'})

@api_view(['POST'])
async def TestMailView(request):
    try:
        data = request.data
        email= data.get('email')
        subject=data.get('subject')
        message=data.get('message')
        link=data.get('link')
        pass
        pass
        pass
        pass


        send_mail(
            subject=f'{subject}',
            message=f'{message}\n forgot password: {link}',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[f'{email}'],
        )
        pass
        return JsonResponse({"result": 'success'})
    except Exception as e:
        return JsonResponse({"result": 'error'})
        pass

@api_view(['GET'])
async def GetOurClients(request):
    try:
        clients = await sync_to_async(OurClients.objects.all)()

        data = []
        for client in clients:
            data.append({
                'image': client.image,
                'name': client.name,
                'index': client.index
            })

        return ServerResponse(
            response=RESPONSE_MESSAGES.success,
            message=RESPONSE_MESSAGES.our_clients_fetch_success,
            data=data,
            code=RESPONSE_CODES.success
        )
    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.our_clients_fetch_error,
            data={'error': str(e)},
            code=RESPONSE_CODES.error
        )

@api_view(['GET'])
async def GetReelSection(request):
    try:
        reels = await sync_to_async(ReelSection.objects.all)()

        data = []
        for reel in reels:
            data.append({
                'video': reel.video,
                'name': reel.name,
                'index': reel.index
            })

        return ServerResponse(
            response=RESPONSE_MESSAGES.success,
            message=RESPONSE_MESSAGES.reel_section_fetch_success,
            data=data,
            code=RESPONSE_CODES.success
        )
    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.reel_section_fetch_error,
            data={'error': str(e)},
            code=RESPONSE_CODES.error
        )


@api_view(['POST'])
@csrf_exempt
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

@api_view(['GET'])
@csrf_exempt
async def RoundRobinPhoneView(request):
	try:
		phone = _get_next_phone()
		return ServerResponse(
			response=RESPONSE_MESSAGES.success,
			message='Phone number retrieved successfully',
			data={'phoneNumber': phone},
			code=RESPONSE_CODES.success
		)
	except Exception as e:
		return ServerResponse(
			response=RESPONSE_MESSAGES.error,
			message='Failed to retrieve phone number',
			data={'error': str(e)},
			code=RESPONSE_CODES.error
		)