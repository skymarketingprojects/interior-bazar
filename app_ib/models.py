import uuid
from django.db import models
from django_quill.fields import QuillField
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
import uuid
from django.db import models,transaction
from .Utils.ModelHelper import indexShifting
from app_ib.Utils.MyMethods import MY_METHODS
from django.utils.text import slugify

from interior_notification.signals import business_changed
from datetime import datetime
from app_ib.Utils.Names import NAMES
from app_ib.Utils.EngineConfig import PLAN_STATUS, PLAN_FAMILY, PLAN_GRANTS, ENTITY_TYPE
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
        
# Create your models here.
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

class BusinessBadge(models.Model):
    type = models.CharField(max_length=250)
    imageUrl = models.URLField(max_length=2250, null=True, blank=True)
    isDefault = models.BooleanField(default=False)

    def __str__(self):
        return f'badge - {self.type}'

class BusinessType(models.Model):
    imageSQUrl = models.CharField(max_length=2250,null=True,blank=True)
    imageRTUrl = models.CharField(max_length=2250,null=True,blank=True)
    value = models.CharField(max_length=250)
    lable = models.CharField(max_length=250)
    trending = models.BooleanField(default=False)
    def __str__(self):
        return f'business type - {self.lable}'

class BusinessCategory(models.Model):
    # businessType = models.ForeignKey(BusinessType, on_delete=models.CASCADE, null=True, blank=True, related_name='business_type_category')
    imageSQUrl = models.CharField(max_length=2250,null=True,blank=True)
    imageRTUrl = models.CharField(max_length=2250,null=True,blank=True)
    value = models.CharField(max_length=250)
    lable = models.CharField(max_length=250)
    shortValue = models.CharField(max_length=250,null=True,blank=True)
    trending = models.BooleanField(default=False)
    index = models.IntegerField(default=0)
    # Reversible hide (task 22): admin can hide a category from public dropdowns
    # without hard-deleting (which would orphan linked businesses).
    isActive = models.BooleanField(default=True)
    def __str__(self):
        return f'business category - {self.lable}'
    def save(self, *args, **kwargs):
        if not self.index:
            self.index = self.__class__.objects.all().count()+1
        indexShifting(instance=self,filter_attr='index')
        super().save(*args, **kwargs)

class BusinessSegment(models.Model):
    businessType = models.ForeignKey(BusinessType, on_delete=models.CASCADE, null=True, blank=True, related_name='business_type_segment')
    businessCategory = models.ManyToManyField(BusinessCategory, blank=True, related_name='business_category_segment')
    imageSQUrl = models.CharField(max_length=2250,null=True,blank=True)
    imageRTUrl = models.CharField(max_length=2250,null=True,blank=True)
    value = models.CharField(max_length=250)
    lable = models.CharField(max_length=250)
    shortValue = models.CharField(max_length=250,null=True,blank=True)
    trending = models.BooleanField(default=False)
    # Reversible hide (task 22): mirrors BusinessCategory.isActive.
    isActive = models.BooleanField(default=True)
    def __str__(self):
        return f'business segment - {self.lable}'

class Business(models.Model):
    user= models.OneToOneField(CustomUser,on_delete=models.CASCADE, null=True, blank=True,related_name='user_business')
    businessName= models.CharField(max_length=250)
    brandName = models.CharField(max_length=250,null=True, blank=True)
    rating= models.CharField(max_length=3,null=True, blank=True,default="3.5")
    whatsapp= models.CharField(max_length=100,default='',null=True, blank=True)
    coverImageUrl = models.TextField(default='',null=True, blank=True)
    bannerImageUrl = models.TextField(default='',null=True, blank=True)
    bannerLink = models.TextField(default='',null=True, blank=True)
    bannerText = models.TextField(default='',null=True, blank=True)
    gst= models.CharField(max_length=250,null=True, blank=True)
    since= models.CharField(max_length=250,null=True, blank=True)

    # segment= models.TextField() # "manufraturer" #remove in version 2
    # catigory= models.TextField() # ["interior", "exterior","office"] # remove in version 2
    businessType= models.ForeignKey(BusinessType, on_delete=models.SET_NULL, null=True, blank=True)
    businessSegment= models.ManyToManyField(BusinessSegment,related_name='business_segment')
    businessCategory= models.ManyToManyField(BusinessCategory,related_name='business_category')

    # badge = models.TextField(null=True, blank=True)
    businessBadge= models.ForeignKey(BusinessBadge, on_delete=models.SET_NULL, null=True, blank=True)
    expertiseTags = models.ManyToManyField("app_ib.Tag", blank=True, related_name="expert_businesses")
    bio = models.TextField( null=True, blank=True)
    timestamp= models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    selfCreated = models.BooleanField(default=False)

    # --- v2.1.0.0 engine fields (additive; legacy `rating` CharField kept as-is) ---
    slug = models.SlugField(max_length=255, null=True, blank=True, unique=True)
    ratingValue = models.FloatField(default=0.0)
    totalReviews = models.PositiveIntegerField(default=0)
    ratingBreakdown = models.JSONField(default=dict, blank=True)
    trendingScore = models.FloatField(default=0.0, db_index=True)
    hotScore = models.FloatField(default=0.0, db_index=True)
    viewCount = models.PositiveIntegerField(default=0)
    leadCount = models.PositiveIntegerField(default=0)
    isVerified = models.BooleanField(default=False)
    completionPercent = models.PositiveIntegerField(default=0)
    canGoLive = models.BooleanField(default=False)
    avgResponseSeconds = models.IntegerField(null=True, blank=True)
    label = models.CharField(max_length=50, blank=True, default='')
    # Geo coordinates for radius (haversine) search on the home filter bar.
    # Additive + nullable: legacy businesses have no coordinates and fall back to
    # city matching (see HomeController._apply_home_filter). Mirrors Shop.lat/lng
    # field style (max_digits=9, decimal_places=6) so the engine treats both alike.
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    # Soft-delete flag (v3 engine CRUD). Default True so every legacy business stays
    # visible; the engine delete_business endpoint flips this to False (reversible).
    # Mirrors Shop.isActive / Architect.isActive so reads can filter the same way.
    isActive = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.businessName) or 'business'
            candidate = base
            n = 1
            while Business.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                n += 1
                candidate = f'{base}-{n}'
            self.slug = candidate
        super().save(*args, **kwargs)

    def __str__(self):
        return f'business name - {self.businessName} : pk: {self.pk}'

class BusinessProfile(models.Model):
    business= models.OneToOneField(Business,on_delete=models.CASCADE, null=True, blank=True,related_name='business_profile')
    # primary_image= models.FileField(null=True, blank=True , upload_to='business/primary_image')
    # secondary_images= models.FileField(null=True, blank=True, upload_to='business/secondary_images')
    primaryImageUrl = models.TextField(default='',null=True, blank=True)
    secondaryImagesUrl = models.TextField(default='',null=True, blank=True)
    about= models.TextField()
    youtubeLink= models.TextField()

    def __str__(self):
        return f'business profile - {self.business.businessName}'

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

class Location(models.Model):
    user= models.OneToOneField(CustomUser,on_delete=models.CASCADE, null=True, blank=True,related_name='user_location')
    business= models.OneToOneField(Business,on_delete=models.CASCADE, null=True, blank=True, related_name='business_location')
    pinCode= models.CharField(max_length=500)
    city= models.CharField(max_length=500)
    locationState = models.ForeignKey(State, on_delete=models.CASCADE,null=True, blank=True)
    # state= models.CharField(max_length=500)
    locationCountry = models.ForeignKey(Country, on_delete=models.CASCADE,null=True, blank=True)
    # country= models.CharField(max_length=500)
    locationLink= models.TextField()
    timestamp= models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.business:
            return f'State: {self.locationState.name}  business location{self.business.pk}'
        elif self.user:
            return f'State: {self.locationState.name}  user location{self.user.pk}'
        return f'State: {self.locationState.name}'

class LeadQuery(models.Model):
    business= models.ForeignKey(Business,on_delete=models.CASCADE, null=True, blank=True,related_name='business_lead_query')
    user= models.ForeignKey(CustomUser,on_delete=models.CASCADE, null=True, blank=True,related_name='user_lead_query')
    name= models.CharField(max_length=500,default='',null=True,blank=True)
    phone= models.CharField(max_length=500,default='',null=True,blank=True)
    email= models.CharField(max_length=500,default='',null=True,blank=True)
    interested= models.TextField(default='',null=True,blank=True)
    query= models.TextField(default='',null=True,blank=True)
    city= models.CharField(max_length=500,default='',null=True,blank=True)
    state= models.CharField(max_length=500,default='',null=True,blank=True)
    country= models.CharField(max_length=500,default='',null=True,blank=True)
    category=models.CharField(max_length=500,default='',null=True,blank=True)
    status= models.TextField(default='',null=True,blank=True)
    leadStatus= models.TextField(default='',null=True,blank=True)
    stage= models.TextField(default='',null=True,blank=True)
    tag= models.TextField(default='',null=True,blank=True)
    priority= models.TextField(default='',null=True,blank=True)
    remark= models.TextField(default='',null=True,blank=True)

    product= models.ForeignKey('interior_products.Product', on_delete=models.SET_NULL, null=True, blank=True,related_name='product_lead_query')
    service = models.ForeignKey('interior_products.Service', on_delete=models.SET_NULL, null=True, blank=True,related_name='service_lead_query')
    catalouge = models.ForeignKey('interior_products.Catelogue', on_delete=models.SET_NULL, null=True, blank=True,related_name='catalouge_lead_query')

    logs = models.JSONField(default=list, null=True, blank=True)
    clientLogs = models.JSONField(default=list, null=True, blank=True,help_text="{'by':'client/business','message':'Text message','date':'date in dmy format(02-12-2026)'}")

    # --- v2.1.0.0 engine fields (additive) ---
    respondedAt = models.DateTimeField(null=True, blank=True)  # first business action on the lead
    sourceChannel = models.CharField(max_length=200, blank=True, default='')
    originType = models.CharField(max_length=50, blank=True, default='')
    originId = models.IntegerField(null=True, blank=True)
    formType = models.CharField(max_length=50, blank=True, default='')
    messageCount = models.PositiveIntegerField(default=0)

    # Qualification (task 13): computed ONCE at creation from the weights
    # singleton (QualificationWeightConfig). Never recomputed on update, so
    # tuning weights only affects NEW leads.
    tier = models.CharField(max_length=1, default='', blank=True, db_index=True)
    score = models.PositiveIntegerField(default=0)

    timestamp= models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_business = self.business
        self._initial_state = self._get_log_state()

    def _get_log_state(self):
        return {
            'business': self.business.businessName if self.business else None,
            'status': self.status,
            'leadStatus': self.leadStatus,
            'stage': self.stage,
            'priority': self.priority,
            'remark': self.remark,
            'tag': self.tag
        }

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        current_state = self._get_log_state()
        events = []

        if is_new:
            events.append("Lead Query Created")
        else:
            for field, old_val in self._initial_state.items():
                new_val = current_state[field]
                if old_val != new_val:
                    events.append(f"{field} updated from '{old_val}' to '{new_val}'")

        if events:
            if not isinstance(self.logs, list):
                self.logs = []
            
            self.logs.append({
                "event": ", ".join(events),
                "timestamp": datetime.now().strftime(NAMES.DMY_12M)
            })

        business_changed_flag = self.pk is not None and self.business != self._original_business

        super().save(*args, **kwargs)  # Save once

        if business_changed_flag:
            business_changed.send(sender=self.__class__, instance=self)

        self._original_business = self.business
        self._initial_state = current_state

    def __str__(self):
        return f'business_id {self.pk}  name: {self.name}  phone{self.phone} date {self.timestamp}'

class Subscription(models.Model):
    type= models.CharField(max_length=800,null=True, blank=True) #listing or #Filter
    # Which entity this plan unlocks (business/shop/architect). Default 'business'
    # so legacy rows + the frozen v1/plan/template/ response stay valid.
    entityType= models.CharField(max_length=50, null=True, blank=True, default='business')
    # Frontend plan category (plans-checkout sidebar): automation/business/shop/architect.
    # 'automation' is the bundle that unlocks all three entity tabs. Defaults to
    # entityType for legacy rows (filled at save() when blank).
    planFamily= models.CharField(max_length=50, null=True, blank=True, default=PLAN_FAMILY.BUSINESS)
    # The entity tabs this plan grants (e.g. automation → ["business","shop","architect"]).
    # Single source of truth for "what does buying this plan unlock" — the entitlement
    # service reads it instead of branching on type. Backfilled from planFamily at save().
    grantsEntityTypes= models.JSONField(default=list, null=True, blank=True)
    # Upgrade-ordering rank (higher = better tier); used by the upgrade flow (Prompt 9).
    tier= models.IntegerField(null=True, blank=True, default=0)
    title= models.CharField(max_length=800,null=True, blank=True)
    subtitle= models.CharField(max_length=800,null=True, blank=True) 
    services= models.TextField()
    duration= models.CharField(max_length=800,null=True, blank=True)
    tag= models.CharField(max_length=800,null=True, blank=True) 
    amount= models.CharField(max_length=800,null=True, blank=True)
    leadcount= models.IntegerField(null=True, blank=True,default=0)
    discountPercentage= models.CharField(max_length=800,null=True, blank=True)
    discountAmount= models.CharField(max_length=800,null=True, blank=True) 
    payableAmount= models.CharField(max_length=800,null=True, blank=True)
    availableDuration = models.JSONField(
        default=list,
        null=True,
        blank=True,
        help_text="List of objects with duration and price. Example: "
                "[{'duration': 3, 'price': 100}, {'duration': 6, 'price': 180}]"
    )
    # ── v3 plans-page display catalogue (promptr2 task 78) ──
    # Display-only: money still flows from `amount`. Rows seeded VERBATIM from the
    # commercial catalogue in migration 0055; per-cycle display strings
    # (price/gstLine/total/oldPrice/savingNote/badgeLabel) live inside
    # availableDuration entries — never computed.
    features = models.JSONField(default=list, blank=True)  # [{"text": …, "subItem"?: …}]
    badge = models.CharField(max_length=100, null=True, blank=True)  # "Most popular" …
    badgeIcon = models.CharField(max_length=100, null=True, blank=True)  # tabler icon name
    # This plan's compare-table column (automation family only):
    # {"column": "Elite ⭐", "popular": true, "values": [{"feature", "value"}]}
    compareRows = models.JSONField(default=dict, blank=True)

    # cover_image= models.FileField(null=True, blank=True, upload_to='subscription/attachment')
    fallbackImageUrl= models.URLField(max_length=2250, null=True, blank=True) 
    # video= models.FileField(null=True, blank=True, upload_to='subscription/video')
    videoUrl= models.URLField(max_length=2250, null=True, blank=True)
    # plan_pdf= models.FileField(null=True, blank=True, upload_to='subscription/pdf')
    planPdfUrl= models.URLField(max_length=2250, null=True, blank=True)

    isActive= models.BooleanField(default=False)
    timestamp= models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f'ID:{self.id} rating:{self.title}'

    def save(self, *args, **kwargs):
        # Backfill the family from the legacy entityType when unset, then derive the
        # granted tabs from the family (automation → all three). Keeps a hand-set
        # grantsEntityTypes (e.g. a custom bundle) untouched.
        if not self.planFamily:
            self.planFamily = self.entityType or PLAN_FAMILY.BUSINESS
        if not self.grantsEntityTypes:
            self.grantsEntityTypes = list(
                PLAN_GRANTS.get(self.planFamily, [self.entityType or ENTITY_TYPE.BUSINESS])
            )
        super().save(*args, **kwargs)


# Shared status<->isActive reconciliation for all purchased plan models. `status` is
# the source of truth; the legacy `isActive` bool is derived from it so old reads keep
# working. Terminal states (cancelled/refunded) are preserved. Call from each save().
def _sync_plan_status(instance):
    if not instance.status:
        instance.status = PLAN_STATUS.PENDING
    instance.isActive = (instance.status == PLAN_STATUS.ACTIVE)


class BusinessPlan(models.Model):
    # Buy-before-entity: a plan is bought by a USER and may exist before the
    # Business is created (business FK stays nullable, filled later in-dashboard).
    user= models.ForeignKey('CustomUser',on_delete=models.CASCADE, null=True, blank=True,related_name='business_plans')
    business= models.ForeignKey(Business,on_delete=models.CASCADE, null=True, blank=True,related_name='business_plan')
    services= models.TextField()
    amount= models.CharField(max_length=500,default='')
    plan = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True)
    # Lifecycle source of truth (pending/active/expired/cancelled/refunded). isActive
    # is the derived legacy shim (isActive == status==active), kept in sync in save().
    status= models.CharField(max_length=20, default=PLAN_STATUS.PENDING, db_index=True)
    isActive= models.BooleanField(default=False)
    transactionId= models.CharField(max_length=500,default='',null=True, blank=True)
    planSummary= models.TextField()
    lastActivate= models.DateTimeField(auto_now_add=True)
    expireDate= models.DateTimeField(null=True, blank=True)
    buyIntent = models.CharField(max_length=1000,null=True, blank=True,default='website')
    timestamp= models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'is_active:{self.isActive} expire_date:{self.expireDate}'

    def save(self, *args, **kwargs):
        _sync_plan_status(self)
        if self.isActive and self.business:
            plans = BusinessPlan.objects.filter(
                business=self.business,
                isActive=True
            ).exclude(id=self.id)
            for plan in plans:
                if int((plan.amount or '0').replace(",", "") or 0) >= int((self.amount or '0').replace(",", "") or 0):
                    self.status = PLAN_STATUS.EXPIRED
                    self.isActive = False
                    continue
                # this plan supersedes a lower active one → retire the lower one
                plan.status = PLAN_STATUS.EXPIRED
                plan.save()

        super().save(*args, **kwargs)

class ShopPlan(models.Model):
    """Per-shop subscription (shops are 1:M per user). Buy-before-entity: bought by
    a USER, links to a Shop later (nullable shop FK). Mirrors BusinessPlan."""
    user= models.ForeignKey('CustomUser',on_delete=models.CASCADE, null=True, blank=True,related_name='shop_plans')
    shop= models.ForeignKey('app_ib.Shop',on_delete=models.CASCADE, null=True, blank=True,related_name='shop_plan')
    services= models.TextField(blank=True, default='')
    amount= models.CharField(max_length=500,default='')
    plan = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True)
    status= models.CharField(max_length=20, default=PLAN_STATUS.PENDING, db_index=True)
    isActive= models.BooleanField(default=False)
    transactionId= models.CharField(max_length=500,default='',null=True, blank=True)
    planSummary= models.TextField(blank=True, default='')
    lastActivate= models.DateTimeField(auto_now_add=True)
    expireDate= models.DateTimeField(null=True, blank=True)
    buyIntent = models.CharField(max_length=1000,null=True, blank=True,default='website')
    timestamp= models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'shop_plan is_active:{self.isActive} expire_date:{self.expireDate}'

    def save(self, *args, **kwargs):
        _sync_plan_status(self)
        super().save(*args, **kwargs)


class ArchitectPlan(models.Model):
    """Architect subscription (1 per user). Buy-before-entity: bought by a USER, links
    to an Architect later (nullable architect FK). Mirrors BusinessPlan."""
    user= models.ForeignKey('CustomUser',on_delete=models.CASCADE, null=True, blank=True,related_name='architect_plans')
    architect= models.ForeignKey('app_ib.Architect',on_delete=models.CASCADE, null=True, blank=True,related_name='architect_plan')
    services= models.TextField(blank=True, default='')
    amount= models.CharField(max_length=500,default='')
    plan = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True)
    status= models.CharField(max_length=20, default=PLAN_STATUS.PENDING, db_index=True)
    isActive= models.BooleanField(default=False)
    transactionId= models.CharField(max_length=500,default='',null=True, blank=True)
    planSummary= models.TextField(blank=True, default='')
    lastActivate= models.DateTimeField(auto_now_add=True)
    expireDate= models.DateTimeField(null=True, blank=True)
    buyIntent = models.CharField(max_length=1000,null=True, blank=True,default='website')
    timestamp= models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'architect_plan is_active:{self.isActive} expire_date:{self.expireDate}'

    def save(self, *args, **kwargs):
        _sync_plan_status(self)
        super().save(*args, **kwargs)


class AutomationPlan(models.Model):
    """Automation BUNDLE subscription. Unlike the single-entity plans, buying it unlocks
    ALL THREE seller tabs (business/shop/architect) — its Subscription.grantsEntityTypes
    is the full set. It is entity-less itself, but carries one nullable FK per entity so a
    single automation purchase can be linked to the user's business + shop + architect as
    each is created. Mirrors the other plan models' lifecycle (status + isActive shim)."""
    user= models.ForeignKey('CustomUser',on_delete=models.CASCADE, null=True, blank=True,related_name='automation_plans')
    business= models.ForeignKey(Business,on_delete=models.SET_NULL, null=True, blank=True,related_name='automation_plan')
    shop= models.ForeignKey('app_ib.Shop',on_delete=models.SET_NULL, null=True, blank=True,related_name='automation_plan')
    architect= models.ForeignKey('app_ib.Architect',on_delete=models.SET_NULL, null=True, blank=True,related_name='automation_plan')
    services= models.TextField(blank=True, default='')
    amount= models.CharField(max_length=500,default='')
    plan = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True)
    status= models.CharField(max_length=20, default=PLAN_STATUS.PENDING, db_index=True)
    isActive= models.BooleanField(default=False)
    transactionId= models.CharField(max_length=500,default='',null=True, blank=True)
    planSummary= models.TextField(blank=True, default='')
    lastActivate= models.DateTimeField(auto_now_add=True)
    expireDate= models.DateTimeField(null=True, blank=True)
    buyIntent = models.CharField(max_length=1000,null=True, blank=True,default='website')
    timestamp= models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'automation_plan is_active:{self.isActive} expire_date:{self.expireDate}'

    def save(self, *args, **kwargs):
        _sync_plan_status(self)
        super().save(*args, **kwargs)


# payment gateway related models
class TransectionData(models.Model):
    orderId= models.CharField(max_length=500,default='')
    transactionId= models.CharField(max_length=500,default='')
    amount= models.CharField(max_length=500,default='')
    paymentFor= models.CharField(max_length=500,default='')
    createdAt = models.DateTimeField()
    expiryAt= models.DateTimeField()
    orderStatus= models.CharField(max_length=500,default='')
    paymentSessionId= models.CharField(max_length=1000,default='')
    # Refund tracking (admin ops console, promptsadmin task 46). Extends this
    # model in place rather than forking the payments schema.
    refundStatus= models.CharField(max_length=50, default='', blank=True)  # '' | REFUNDED | REJECTED
    refundAmount= models.CharField(max_length=500, default='', blank=True)
    refundReason= models.TextField(default='', blank=True)
    refundedAt= models.DateTimeField(null=True, blank=True)
    refundedBy= models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='refunds_actioned')
    # Manual-payment verification (promptsadmin task 11). 'manual' rows carry a
    # SUBMITTED->PAID/REJECTED lifecycle in orderStatus, verified by an admin.
    paymentMethod= models.CharField(max_length=20, default='gateway')  # 'gateway' | 'manual'
    proofUrl= models.TextField(default='', blank=True)  # buyer-uploaded UPI/NEFT payment proof (manual)
    verifiedBy= models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='payments_verified')
    verifiedAt= models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f" transection data for {self.paymentFor} with transaction id {self.transactionId}"
    
# Platform own Plan buy query
class PlanQuery(models.Model):
    user= models.ForeignKey(CustomUser,on_delete=models.CASCADE, null=True, blank=True)
    plan= models.CharField(max_length=500,default='')
    name= models.CharField(max_length=500,default='')
    email= models.CharField(max_length=500,default='')
    phone= models.CharField(max_length=500,default='')
    state= models.CharField(max_length=500,default='')
    country= models.CharField(max_length=500,default='')
    address= models.TextField(default='')
    transactionId= models.CharField(max_length=500,default='')
    stage= models.CharField(max_length=500,default='') #{"1":"Lead","2":"Contacted","3":"Followed Up","4":"Closed"}
    attachment= models.FileField(null=True, blank=True, upload_to='lead_query/attachment')
    attachmentUrl = models.URLField(default='',null=True, blank=True)
    timestamp= models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f' ID {self.pk} phone:{self.phone} stage:{self.stage}'
        
# Plan Buy Quate related to service
class Quate(models.Model):
    leadType = models.CharField(max_length=500,default='')
    businessType = models.CharField(max_length=500,default='')
    budget= models.CharField(max_length=500,default='')
    name= models.CharField(max_length=500,default='')
    phoneNumber= models.CharField(max_length=500,default='')
    query= models.TextField(default='')
    email= models.CharField(max_length=500,default='')
    noOfEmp = models.CharField(max_length=500,default='')
    companyName = models.CharField(max_length=500,default='')
    note= models.CharField(max_length=500,default='')
    stage= models.CharField(max_length=500,default='') #{"1":"Lead","2":"Contacted","3":"Followed Up","4":"Closed"} Admin
    city= models.CharField(max_length=500,default='')
    state= models.CharField(max_length=500,default='')
    timestamp= models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.phoneNumber and not self.stage:
            return f'ID {self.pk} phone:{self.phoneNumber}'
        elif self.phoneNumber and self.stage:
            return f'ID {self.pk} phone:{self.phoneNumber} stage:{self.stage}'
        return f'ID {self.pk}'
    
    class Meta:
        verbose_name = "Leads for company"
        verbose_name_plural = "Platform Own Leads"

class Feedback(models.Model):
    user= models.ForeignKey(CustomUser,on_delete=models.CASCADE, null=True, blank=True)
    contact= models.CharField(max_length=500) # lable : Contact detail 
    feedback= models.TextField() # lable : Feedback rating
    status= models.TextField() # lable : [view,]
    timestamp= models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'pk:{self.pk}  feedback:{self.feedback}'

class Blog(models.Model):
    user= models.ForeignKey(CustomUser,on_delete=models.CASCADE, null=True, blank=True)
    title= models.TextField()
    slug = models.CharField(max_length=800, unique=True, null=True, blank=True)
    cover= models.FileField(null=True, blank=True,upload_to='blog/cover')
    coverImageUrl = models.TextField(default='',null=True, blank=True)
    description=QuillField(null=True, blank=True)
    author= models.TextField()
    authorImageUrl = models.URLField(default='',null=True, blank=True)
    isFeatured = models.BooleanField(default=False)
    featuredOrder = models.PositiveIntegerField(default=0)
    metaTitle = models.CharField(max_length=300, blank=True, default='')
    metaDescription = models.TextField(blank=True, default='')
    focusKeyword = models.CharField(max_length=200, blank=True, default='')
    status = models.CharField(max_length=10, choices=(('draft', 'draft'), ('published', 'published')), default='draft')
    timestamp= models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'author {self.author} title:{self.title} timestamp:{self.timestamp}'
    
    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            self.slug = MY_METHODS.generate_slug(self.title)
        super().save(*args, **kwargs)

class Contact(models.Model):
    tag= models.TextField()
    name= models.CharField(max_length=800,null=True, blank=True) 
    phone= models.CharField(max_length=800,null=True, blank=True) 
    mail= models.CharField(max_length=800,null=True, blank=True) 
    company= models.CharField(max_length=800,null=True, blank=True) 
    recognisation= models.CharField(max_length=800,null=True, blank=True) 
    detail= models.TextField()
    attachment= models.FileField(null=True, blank=True,upload_to='contact/attachment')
    timestamp= models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'ID {self.pk} tag {self.tag}'

class NewsletterSubscriber(models.Model):
    """Email newsletter subscribers — sourced from blog / landing pages."""
    email = models.EmailField(unique=True)
    user = models.ForeignKey(CustomUser, null=True, blank=True, on_delete=models.SET_NULL, related_name="newsletter_subs")
    source = models.CharField(max_length=30, default="blog")
    isConfirmed = models.BooleanField(default=False)
    isActive = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"NewsletterSubscriber {self.email} (confirmed={self.isConfirmed})"


class Constants(models.Model):
    segments= models.TextField() # {'manu':Manugraturer, 'retailer':Retailer}
    catigory= models.TextField() # {'manu':[furniture,lighting,decor,flooring,wall_coverings,window_treatments,home_textiles,kitchen_cabinets], 'retailer':[bathroom_fixtures,toilets,faucets,sinks,showers,bathtubs,bathroom_accessories,water_systems]}
    paymentDetail = models.TextField()
    paymentQr = models.FileField(null=True, blank=True ,upload_to='payment_qr')
    def __str__(self):
        return f' pk {self.pk} segments:{self.segments}'

class Banners(models.Model):
    supportText = models.TextField()
    title = models.TextField()
    banner = models.FileField(null=True, blank=True ,upload_to='banners')
    # Admin ops console (promptsadmin task 15): S3 URL uploaded client-side
    # (new banners) + display order for the reorder controls.
    bannerUrl = models.URLField(max_length=1000, default='', blank=True)
    order = models.PositiveIntegerField(default=0, db_index=True)
    isActive = models.BooleanField(default=False)
    def __str__(self):
        return f' pk {self.pk} title:{self.title}'
    class Meta:
        ordering = ['order', 'id']

class OfferHeading(models.Model):
    title = models.TextField()
    isActive = models.BooleanField(default=False)
    def __str__(self):
        return f' pk {self.pk} title:{self.title}'

class Pages(models.Model):
    pageName = models.CharField(max_length=500, unique=True)
    title = models.CharField(max_length=500)
    content = QuillField(null=True, blank=True)
    def __str__(self):
        return f'page_name: {self.pageName} title:{self.title}'
    class Meta:
        verbose_name_plural = "information pages"
    
class QNA(models.Model):
    question = models.TextField()
    answer = models.TextField()
    isActive = models.BooleanField(default=False)
    def __str__(self):
        return f' pk {self.pk} question:{self.question}'
    
# Create your models here.
class Page(models.Model):
    name = models.CharField(max_length=255)


    def __str__(self):
        return f"Page {self.name}"
    class Meta:
        verbose_name_plural = "stockimages page"
    
class Section(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"Section {self.name}"

class StockMedia(models.Model):
    image = models.URLField(max_length=2250, null=True, blank=True)
    video = models.URLField(max_length=2250, null=True, blank=True)
    page = models.ForeignKey(Page, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True)
    index = models.IntegerField(default=1)


    def __str__(self):
        if self.page and self.section:
            return f"StockMedia {self.pk} | Page: {self.page.name} | Section: {self.section.name} | Index: {self.index}"
        elif self.page:
            return f"StockMedia {self.pk} | Page: {self.page.name} | Index: {self.index}"
        elif self.section:
            return f"StockMedia {self.pk} | Section: {self.section.name} | Index: {self.index}"
        return f"StockMedia {self.pk} | Index: {self.index}"
    
#offer text
class OfferText(models.Model):
    text = QuillField(null=True, blank=True)
    link = models.URLField(max_length=2250, null=True, blank=True)
    color = models.CharField(max_length=100, default='', null=True, blank=True)
    show = models.BooleanField(default=False)
    def __str__(self):
        return f' pk {self.pk} text:{self.text}'

#funnel form
class FunnelForm(models.Model):
    name = models.CharField(max_length=255, default='', null=True, blank=True)
    companyName = models.CharField(max_length=255, default='', null=True, blank=True)
    email = models.CharField(max_length=255, default='', null=True, blank=True)
    phone = models.CharField(max_length=255, default='', null=True, blank=True)
    planType = models.CharField(max_length=255, default='', null=True, blank=True)
    plan = models.CharField(max_length=255, default='', null=True, blank=True)
    intrest = models.TextField(default='', null=True, blank=True)
    need = models.TextField(default='', null=True, blank=True)
    timestamp= models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=255, default='New', null=True, blank=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f' pk {self.pk} name:{self.name} phone:{self.phone}'

class SocialMedia(models.Model):
    name= models.CharField(max_length=250)

    def __str__(self):
        return f'social media - {self.name}'

# Business Social Media
class BusinessSocialMedia(models.Model):
    business= models.ForeignKey(Business,on_delete=models.CASCADE,related_name='businessSocialMedia')
    socialMedia= models.ForeignKey(SocialMedia,on_delete=models.CASCADE,related_name='socialMediaBusiness')
    link= models.TextField()

    def __str__(self):
        return f'business social media - {self.business.pk} - {self.socialMedia.name}'

class DaySchedule(models.Model):
    DAYS_OF_WEEK = [
        (1, 'Monday'),
        (2, 'Tuesday'),
        (3, 'Wednesday'),
        (4, 'Thursday'),
        (5, 'Friday'),
        (6, 'Saturday'),
        (7, 'Sunday'),
    ]

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="schedules")
    day = models.PositiveSmallIntegerField(choices=DAYS_OF_WEEK)
    startTime = models.TimeField()
    endTime = models.TimeField()
    isWorking = models.BooleanField(default=False)

    class Meta:
        ordering = ['day']

    def __str__(self):
        return f"{self.business.businessName} - {self.get_day_display()}"


class OurClients(models.Model):
    image = models.URLField(max_length=2250)
    name = models.CharField(max_length=2250)
    index = models.IntegerField(default=1, null=True, blank=True)

    def __str__(self):
        return f' pk {self.pk} name:{self.name}'
    
    def save(self, *args, **kwargs):
        if not self.index:
            self.index = self.__class__.objects.all().count()+1
        indexShifting(instance=self,filter_attr='index')
        super().save(*args, **kwargs)

class ReelSection(models.Model):
    video = models.URLField(max_length=2250)
    name = models.CharField(max_length=2250)
    index = models.IntegerField(default=1, null=True, blank=True)

    def __str__(self):
        return f' pk {self.pk} name:{self.name}'
    
    def save(self, *args, **kwargs):
        if not self.index:
            self.index = self.__class__.objects.all().count()+1
        indexShifting(instance=self,filter_attr='index')
        super().save(*args, **kwargs)

# --- v2.1.0.0 engine models (Shop, Architect, Review, ViewEvent, TrendingScore, ...) ---
from app_ib.engine_models import *  # noqa: E402,F401,F403
