import random
from ast import Pass
import time
from types import SimpleNamespace
import json
import re
from django.conf import settings
from django.core.mail import send_mail
from app_ib.Utils.AppMode import APPMODE



class MY_METHODS:

    @staticmethod
    async def formatAmount(input_value):
        if not isinstance(input_value, str):
            input_value = str(input_value)
        cleaned = re.sub(r"[^0-9.]", "", input_value)

        parts = cleaned.split(".")

        if len(parts) > 2:
            valid_number = f"{parts[0]}.{parts[1]}"
        else:
            valid_number = cleaned

        try:
            parsed = float(valid_number)
        except ValueError:
            return 0.0

        return round(parsed, 2)

    @staticmethod
    async def getCurrentDateTime():
        return time.localtime(time.time())
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
    def generate_slug(text, randomize=True):
        
        # Convert to lowercase
        text = text.lower()

        # Replace spaces and underscores with hyphens
        text = re.sub(r'[\s_]+', '-', text)

        # Remove non-alphanumeric characters except hyphens
        text = re.sub(r'[^a-z0-9-]', '', text)

        # Remove leading/trailing hyphens
        text = text.strip('-')

        # Optionally add a random 4-digit number
        if randomize:
            rand_num = random.randint(1000, 9999)
            text = f"{text}-{rand_num}"

        return text

    @staticmethod
    def unslugify(slug):
        """
        Convert a slug back to a human-readable string.
        - Removes trailing random number if present.
        - Replaces hyphens with spaces.
        - Capitalizes each word.
        """
        # Remove trailing "-1234" pattern (random 4-digit number)
        slug = re.sub(r'-\d{4}$', '', slug)

        # Replace hyphens with spaces
        words = slug.replace('-', ' ').split()

        # Capitalize each word
        return ' '.join(word.capitalize() for word in words)

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
        
    @staticmethod
    async def printStatus(status):
        if settings.ENV == APPMODE.PROD:
            return 0
        else:
            print(status)
    
