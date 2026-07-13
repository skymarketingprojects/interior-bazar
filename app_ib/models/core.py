"""app_ib core models — auth/user identity + per-device sessions.

These are the permanent app_ib stayers (CustomUser is AUTH_USER_MODEL). The old
AdPage/PlatformAd ad models were removed in TASK 22 — the single ad system is
interior_advertisement.AdCampaign.
"""
import uuid
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils.text import slugify

USER = settings.AUTH_USER_MODEL


# Custom User Manager
class CustomUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("The Username field must be set")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)  # securely hashes the password
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)


# Custom User Model
class CustomUser(AbstractBaseUser, PermissionsMixin):
    my_id = models.TextField()
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    username = models.CharField(max_length=500, unique=True)
    type = models.CharField(max_length=128)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # Needed for Django admin
    is_delete = models.BooleanField(default=False)
    isVerified = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    selfCreated = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)  # From AbstractBaseUser but can override
    text_password = models.CharField(max_length=500, default='Test@123', null=True, blank=True)
    # Columns already exist in deployed DBs as NOT NULL without a DB default —
    # the model must supply values on INSERT or user creation fails
    preferred_language = models.CharField(max_length=10, default='en')
    preferred_currency = models.CharField(max_length=3, default='INR')
    # Buyer dashboard "Settings": notification + privacy preference toggles (task 49).
    settings = models.JSONField(default=dict, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'       # Login with username
    REQUIRED_FIELDS = []              # Extra required fields when creating superusers

    def __str__(self):
        return f'date: {self.timestamp} username: {self.username}'

    def save(self, *args, **kwargs):
        if not self.unique_id:
            self.unique_id = uuid.uuid4()
        if not self.my_id:
            self.my_id = f"{slugify(self.username)}-{uuid.uuid4()}"
        super().save(*args, **kwargs)


class UserProfile(models.Model):
    user= models.OneToOneField(CustomUser,on_delete=models.CASCADE, null=True, blank=True,related_name='user_profile')
    name= models.CharField(max_length=250,default='',null=True, blank=True)
    phone= models.CharField(max_length=100,default='',null=True, blank=True)
    countryCode= models.CharField(max_length=10,default='',null=True, blank=True)
    email= models.CharField(max_length=250,default='',null=True, blank=True)
    # profile_image= models.FileField(null=True, blank=True, upload_to='user/profile_image')
    profileImageUrl = models.TextField(default='',null=True, blank=True)
    timestamp= models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'profile - {self.user.pk}'


class Country(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=10)

    def __str__(self):
        return f'Country: {self.name} ({self.code})'


class State(models.Model):
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='states')
    name = models.CharField(max_length=255)
    value = models.CharField(max_length=255,null=True, blank=True)

    def __str__(self):
        return f'State: {self.name} in {self.country.name}'


class UserSession(models.Model):
    """Tracks per-device JWT sessions for the active-sessions dashboard."""
    user = models.ForeignKey(USER, on_delete=models.CASCADE, related_name="sessions")
    jti = models.CharField(max_length=64, blank=True, default="", db_index=True)
    deviceLabel = models.CharField(max_length=120, blank=True, default="")
    userAgent = models.TextField(blank=True, default="")
    ipAddress = models.GenericIPAddressField(null=True, blank=True)
    city = models.CharField(max_length=100, blank=True, default="")
    lastActiveAt = models.DateTimeField(auto_now=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    revokedAt = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "app_ib"
        ordering = ["-lastActiveAt"]
        indexes = [
            models.Index(fields=["user", "revokedAt"]),
        ]

    def __str__(self):
        return f"UserSession user={self.user_id} jti={self.jti[:12]}… ({self.deviceLabel or 'unknown'})"
