import random
from ast import Pass
import time
from types import SimpleNamespace
import json
import re
from django.conf import settings
from django.core.mail import send_mail
from app_ib.Utils.AppMode import APPMODE
from django.utils import timezone
from datetime import timedelta
from math import ceil
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
class MY_METHODS:

    @staticmethod
    async def getReadTime(content):
        words = content.split()
        read_time = len(words) // 200 + 1
        return read_time

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
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
            )
            # await MY_METHODS.printStatus('Email sent successfully!')
            return True
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error sending email: {e}')
            return False
        
    @staticmethod
    async def printStatus(status):
        if settings.ENV == APPMODE.PROD:
            return 0
        else:
            print(status)

    @staticmethod
    async def get_time_ago(updated_at):
        if updated_at:
            # Calculate the time difference between now and updated_at
            time_diff = timezone.now() - updated_at
            # await MY_METHODS.printStatus(f'time_diff {time_diff}')

            # Determine the number of seconds, minutes, hours, and days
            if time_diff < timedelta(minutes=1):
                return "Just now"
            elif time_diff < timedelta(hours=1):
                minutes = time_diff.seconds // 60
                return f"{minutes} min{'s' if minutes > 1 else ''}"
            elif time_diff < timedelta(days=1):
                hours = time_diff.seconds // 3600
                return f"{hours} hr{'s' if hours > 1 else ''}"
            elif time_diff < timedelta(weeks=1):
                days = time_diff.days
                return f"{days} day{'s' if days > 1 else ''}"
            elif time_diff < timedelta(weeks=4):
                weeks = time_diff.days // 7
                return f"{weeks} week{'s' if weeks > 1 else ''}"
            else:
                months = time_diff.days // 30
                return f"{months} month{'s' if months > 1 else ''}"
        return "No update available"
    
    @staticmethod
    async def paginate_queryset(queryset, page=1, size=10):
        """Paginate queryset using Django's Paginator and return PascalCase pagination."""
        try:
            paginator = Paginator(queryset, size)
            
            try:
                page_obj = paginator.page(page)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)

            results = list(page_obj.object_list)  # convert queryset slice to list if needed

            return {
                "results": results,
                "pagination": {
                    "pageNo": page_obj.number,
                    "pageSize": size,
                    "totalItems": paginator.count,
                    "totalPages": paginator.num_pages,
                    "hasNext": page_obj.has_next(),
                    "hasPrev": page_obj.has_previous()
                }
            }
        except Exception as e:
            print(f"Pagination error: {e}")
            return {
                "results": [],
                "pagination": {
                    "pageNo": 1,
                    "pageSize": size,
                    "totalItems": 0,
                    "totalPages": 0,
                    "hasNext": False,
                    "hasPrev": False
                }
            }
        
    @staticmethod
    async def parseDurationToDays(duration):
        """
        Convert a duration (int or string like '2 days', '1 month', '3 years')
        into number of days (int).
        """
        # If it's already an integer, return it directly
        if isinstance(duration, int):
            return duration

        # If it's a numeric string, return its int value
        if isinstance(duration, str) and duration.strip().isdigit():
            return int(duration)

        # Parse string formats like "2 day", "3 days", "1 month", "2 years"
        match = re.match(r"(\d+)\s*(day|days|month|months|year|years)?", duration.strip().lower())
        if not match:
            raise ValueError(f"Invalid duration format: {duration}")

        value = int(match.group(1))
        unit = match.group(2) or "days"  # Default to days if no unit specified

        # Convert everything to days
        if unit in ["day", "days"]:
            return value
        elif unit in ["month", "months"]:
            return value * 30  # approximate
        elif unit in ["year", "years"]:
            return value * 365
        else:
            raise ValueError(f"Unknown time unit: {unit}")


    import re

    @staticmethod
    async def formatPhone(phone: str, country_code: str) -> str | None:
        """
        Cleans, formats, and validates a phone number into international (E.164) format.
        
        Args:
            phone (str): The input phone number (can be messy or local format).
            country_code (str): Country code, with or without '+' (e.g. '91' or '+91').

        Returns:
            str | None: Formatted international phone number (e.g. '+919090407368')
                        or None if invalid.
        """
        if not phone or not isinstance(phone, str):
            return None

        try:
            # Normalize country_code (remove '+' if present)
            country_code = re.sub(r"[^\d]", "", country_code or "")

            phone = phone.strip()

            # Already in international format
            if re.match(r"^\+\d{10,15}$", phone):
                return phone

            # Remove all non-digit characters
            cleaned = re.sub(r"[^\d]", "", phone)

            # Handle '00' prefix
            if cleaned.startswith("00"):
                cleaned = cleaned[2:]

            # Remove leading zeros (common in local formats)
            cleaned = cleaned.lstrip("0")

            # Prepend country code if missing
            if not cleaned.startswith(country_code):
                cleaned = f"{country_code}{cleaned}"

            # Add '+' prefix
            formatted = f"+{cleaned}"

            # Validate final format (E.164)
            if re.match(r"^\+\d{10,15}$", formatted):
                return formatted

            return None

        except Exception:
            return None
    @staticmethod
    def formatPhoneInternational(phone: str, country_code: str) -> str | None:
        """
        Cleans, formats, and validates a phone number into international (E.164) format.
        
        Args:
            phone (str): The input phone number (can be messy or local format).
            country_code (str): Country code, with or without '+' (e.g. '91' or '+91').

        Returns:
            str | None: Formatted international phone number (e.g. '+919090407368')
                        or None if invalid.
        """
        if not phone or not isinstance(phone, str):
            return None

        try:
            # Normalize country_code (remove '+' if present)
            country_code = re.sub(r"[^\d]", "", country_code or "")

            phone = phone.strip()

            # Already in international format
            if re.match(r"^\+\d{10,15}$", phone):
                return phone

            # Remove all non-digit characters
            cleaned = re.sub(r"[^\d]", "", phone)

            # Handle '00' prefix
            if cleaned.startswith("00"):
                cleaned = cleaned[2:]

            # Remove leading zeros (common in local formats)
            cleaned = cleaned.lstrip("0")

            # Prepend country code if missing
            if not cleaned.startswith(country_code):
                cleaned = f"{country_code}{cleaned}"

            # Add '+' prefix
            formatted = f"+{cleaned}"

            # Validate final format (E.164)
            if re.match(r"^\+\d{10,15}$", formatted):
                return formatted

            return None

        except Exception:
            return None
    @staticmethod
    async def getRandomNumber(min_val=1, max_val=999):
        """Generate a random number between min_val and max_val."""
        return str(random.randint(min_val, max_val))