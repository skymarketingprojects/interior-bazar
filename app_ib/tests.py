from django.conf import settings
from django.core.mail import send_mail
import httpx
import asyncio
from django.http import JsonResponse
from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from django.test import TestCase


# Create your tests here.
@api_view(['POST'])
async def TestMailView():
    try:
        send_mail(
            subject='Test Subject',
            message='Hello! This is a test email from Django using Gmail.',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=['vishalshakaya.feelsafe@gmail.com'],
        )
        print('Email sent successfully!')
    except Exception as e:
        print(f'Email sending failed: {e}')
