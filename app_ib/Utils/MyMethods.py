import random
from ast import Pass
import time
from types import SimpleNamespace
import json
import re

from django.conf import settings
from django.core.mail import send_mail

from app_ib.models import CustomUser


class MY_METHODS:
    @staticmethod
    async def get_random_rating():
        rating = random.uniform(3, 5)
        return round(rating, 1)  # round to 1 decimal place

    @staticmethod
    def GetCurrentTimeinStr():
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))

    @staticmethod
    def GetCurrentTimeinInt():
        return int(time.time())
    
    @staticmethod
    async def GetTimeDifferenceInMinutes(my_time):
        timestamp = time.strptime(my_time, "%Y-%m-%d %H:%M:%S")
        current_struct = time.localtime(time.time())
        diff_sec = time.mktime(current_struct) - time.mktime(timestamp)
        diff_min = diff_sec / 60
        return int(diff_min)

    @staticmethod
    def json_to_object(json_data):
        """
        Convert a JSON string or dictionary to a dot notation object.
        """
        if isinstance(json_data, str):
            json_data = json.loads(json_data)

        def convert(item):
            if isinstance(item, dict):
                return type('JSONObject', (), {k: convert(v) for k, v in item.items()})()
            elif isinstance(item, list):
                return [convert(i) for i in item]
            else:
                return item
        return convert(json_data)


    @staticmethod
    def object_to_json(obj):
        def convert(item):
            if isinstance(item, list):
                return [convert(i) for i in item]
            elif isinstance(item, dict):
                return {k: convert(v) for k, v in item.items()}
            elif hasattr(item, "__dict__"):
                return {k: convert(v) for k, v in item.__dict__.items()}
            else:
                return item

        return json.dumps(convert(obj), default=str, indent=4)
    
    @staticmethod
    def _validate_email(email):
        """
        Validates an email address using regex.
        Returns True if valid, False otherwise.
        """
        pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
        return bool(re.fullmatch(pattern, email))

    @staticmethod
    def _validate_phone(phone):
        """
        Validate phone number against international E.164 format:
        + followed by 7 to 15 digits, optional spaces allowed.
        """
        pattern = r'^\+(?:[0-9] ?){6,14}[0-9]$'
        return bool(re.match(pattern, phone))
    
    @staticmethod
    def _validate_gst(gst):
        """Returns True if GSTIN is valid in format, False otherwise."""
        pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
        return bool(re.match(pattern, gst.upper()))


    @staticmethod
    async def send_email(email, subject, message):
        """Send email using SMTP"""
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
        )
        try:
            return True
        except Exception as e:
            print(f'Error in send_email {e}')
            return False
    
  