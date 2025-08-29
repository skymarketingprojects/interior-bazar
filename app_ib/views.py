from django.core.mail import send_mail
import httpx
import asyncio
from django.http import JsonResponse
from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from django.conf import settings

# Create your views here.
@api_view(['GET'])
async def TestView(request):
    try:
        # file = request.data.get("lawyer_profile_image")
        # compress_image = await asyncio.gather(helpingMethos.MyImageCompression(type=COMPRESSSION_TYPE.LAWYER_PROFILE, image=file))
        # print(f'compress_image {compress_image[0]}')
        return JsonResponse({"result": 'success'})

    except Exception as e:
        print(f'{e}')
        return JsonResponse({"result": 'fail'})

@api_view(['POST'])
async def TestMailView(request):
    try:
        data = request.data
        email= data.get('email')
        subject=data.get('subject')
        message=data.get('message')
        link=data.get('link')
        print(f'email {email}')
        print(f'subject {subject}')
        print(f'message {message}')
        print(f'link {link}')


        send_mail(
            subject=f'{subject}',
            message=f'{message}\n forgot password: {link}',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[f'{email}'],
        )
        print('Email sent successfully!')
        return JsonResponse({"result": 'success'})
    except Exception as e:
        return JsonResponse({"result": 'error'})
        print(f'Email sending failed: {e}')