"""interior_business models — the Business cluster + Location, moved here from
app_ib in TASK 18 (state-only; db_table pinned so the physical tables are
untouched). Cross-app FKs (CustomUser/State/Country in app_ib, Tag in
interior_engine) use string refs so this file never imports app_ib.models →
no cycle. `from app_ib.models import Business` still resolves via the compat
re-export in app_ib/models/__init__.py.
"""
from django.db import models
from django.utils.text import slugify
from app_ib.Utils.ModelHelper import indexShifting


class BusinessBadge(models.Model):
    type = models.CharField(max_length=250)
    imageUrl = models.URLField(max_length=2250, null=True, blank=True)
    isDefault = models.BooleanField(default=False)

    def __str__(self):
        return f'badge - {self.type}'

    class Meta:
        db_table = "app_ib_businessbadge"


class BusinessType(models.Model):
    imageSQUrl = models.CharField(max_length=2250,null=True,blank=True)
    imageRTUrl = models.CharField(max_length=2250,null=True,blank=True)
    value = models.CharField(max_length=250)
    lable = models.CharField(max_length=250)
    trending = models.BooleanField(default=False)
    def __str__(self):
        return f'business type - {self.lable}'

    class Meta:
        db_table = "app_ib_businesstype"


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

    class Meta:
        db_table = "app_ib_businesscategory"


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

    class Meta:
        db_table = "app_ib_businesssegment"


class Business(models.Model):
    user= models.OneToOneField("app_ib.CustomUser",on_delete=models.CASCADE, null=True, blank=True,related_name='user_business')
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
    expertiseTags = models.ManyToManyField("interior_engine.Tag", blank=True, related_name="expert_businesses")
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
    # --- trust/quality signals (additive; user-approved 2026-07-15) ---
    # avgProjectValue → KPI grid 4th cell; the two flags → credentials grid.
    # All nullable/false so existing businesses are untouched and the UI shows
    # each only when set.
    avgProjectValue = models.PositiveIntegerField(null=True, blank=True,
        help_text="Average project value in rupees. null = cell omitted from the KPI grid.")
    coaRegistered = models.BooleanField(default=False,
        help_text="Council-of-Architecture registered → 'COA registered' credential chip.")
    liabilityInsured = models.BooleanField(default=False,
        help_text="Carries liability insurance → 'Liability insured' credential chip.")
    # --- Business profile-wizard fields (F1, user-approved 2026-07-16, additive) ---
    # The 4-step wizard collected these but persist() discarded them. All nullable/
    # blank so existing rows are untouched; the seller form fills them over time.
    cin = models.CharField(max_length=50, blank=True, default='', help_text="Company Identification Number.")
    pan = models.CharField(max_length=20, blank=True, default='', help_text="PAN.")
    udyam = models.CharField(max_length=50, blank=True, default='', help_text="Udyam / MSME registration number.")
    founderName = models.CharField(max_length=200, blank=True, default='')
    teamSize = models.CharField(max_length=50, blank=True, default='')
    businessModel = models.CharField(max_length=50, blank=True, default='')
    productPriceTiers = models.JSONField(default=list, blank=True, help_text="Product price-tier labels the seller serves.")
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

    class Meta:
        db_table = "app_ib_business"


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

    class Meta:
        db_table = "app_ib_businessprofile"


class Location(models.Model):
    user= models.OneToOneField("app_ib.CustomUser",on_delete=models.CASCADE, null=True, blank=True,related_name='user_location')
    business= models.OneToOneField(Business,on_delete=models.CASCADE, null=True, blank=True, related_name='business_location')
    pinCode= models.CharField(max_length=500)
    city= models.CharField(max_length=500)
    locationState = models.ForeignKey("app_ib.State", on_delete=models.CASCADE,null=True, blank=True)
    # state= models.CharField(max_length=500)
    locationCountry = models.ForeignKey("app_ib.Country", on_delete=models.CASCADE,null=True, blank=True)
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

    class Meta:
        db_table = "app_ib_location"


class SocialMedia(models.Model):
    name= models.CharField(max_length=250)

    def __str__(self):
        return f'social media - {self.name}'

    class Meta:
        db_table = "app_ib_socialmedia"


# Business Social Media
class BusinessSocialMedia(models.Model):
    business= models.ForeignKey(Business,on_delete=models.CASCADE,related_name='businessSocialMedia')
    socialMedia= models.ForeignKey(SocialMedia,on_delete=models.CASCADE,related_name='socialMediaBusiness')
    link= models.TextField()

    def __str__(self):
        return f'business social media - {self.business.pk} - {self.socialMedia.name}'

    class Meta:
        db_table = "app_ib_businesssocialmedia"


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
        db_table = "app_ib_dayschedule"
        ordering = ['day']

    def __str__(self):
        return f"{self.business.businessName} - {self.get_day_display()}"
