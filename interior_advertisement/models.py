import uuid
from django.db import models
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

# ===== ENUM TABLES =====

class AdStatus(models.Model):
    code = models.CharField(max_length=50, unique=True)  # e.g. 'draft'
    label = models.CharField(max_length=100)             # e.g. 'Draft'

    def __str__(self):
        return self.label


class AdApprovalMode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    label = models.CharField(max_length=100)

    def __str__(self):
        return self.label


class AdAssetType(models.Model):
    code = models.CharField(max_length=50, unique=True)  # e.g. 'image'
    label = models.CharField(max_length=100)             # e.g. 'Image Asset'

    def __str__(self):
        return self.label


class AdPaymentStatus(models.Model):
    code = models.CharField(max_length=50, unique=True)
    label = models.CharField(max_length=100)

    def __str__(self):
        return self.label


class AdEventType(models.Model):
    code = models.CharField(max_length=50, unique=True)  # e.g. 'impression'
    label = models.CharField(max_length=100)

    def __str__(self):
        return self.label


# ===== CORE TABLES =====

class AdPlacement(models.Model):
    ratioChoices=[
        ('16:9', '16:9'),
        ('4:3', '4:3'),
        ('1:1', '1:1'),
    ]
    placementId = models.SmallIntegerField(primary_key=True)
    code = models.CharField(max_length=100, unique=True)  # e.g. home_carousel
    dailyPrice = models.DecimalField(max_digits=10, decimal_places=2)
    aspectRatio = models.CharField(max_length=100, choices=ratioChoices, default='1:1')

    def __str__(self):
        return self.code


class AdCampaign(models.Model):
    advertiser = models.ForeignKey('app_ib.Business', on_delete=models.CASCADE, related_name='adCampaigns')
    title = models.CharField(max_length=255, blank=True, null=True)
    placement = models.ForeignKey(AdPlacement, on_delete=models.CASCADE, related_name='adCampaigns')
    startDate = models.DateTimeField()
    endDate = models.DateTimeField()
    days = models.IntegerField()
    priceTotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    status = models.ForeignKey(AdStatus, on_delete=models.PROTECT)
    approvalMode = models.ForeignKey(AdApprovalMode, on_delete=models.PROTECT)

    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)
    # Admin ad-moderation reject reason (promptsadmin task 16).
    rejectReason = models.TextField(default='', blank=True)

    def __str__(self):
        return f"{self.title or 'Untitled'} ({self.status.code})"
    
    def getDays(self):  
        if self.days and self.days > 0:
            return self.days

        if self.startDate and self.endDate:
            try:
                delta = self.endDate.date() - self.startDate.date()
                return max(delta.days + 1, 0)
            except Exception:
                return 0
        return 0


class AdAsset(models.Model):
    campaign = models.ForeignKey(AdCampaign, on_delete=models.CASCADE, related_name='assets')
    assetType = models.ForeignKey(AdAssetType, on_delete=models.PROTECT)
    category = models.ManyToManyField('app_ib.BusinessCategory')
    subCategory = models.ManyToManyField('app_ib.BusinessSegment')
    productCategory = models.ManyToManyField("interior_products.ProductCategory")
    productSubCategory = models.ManyToManyField("interior_products.ProductSubCategory")
    s3Key = models.TextField()
    meta = models.JSONField(default=dict)

    def __str__(self):
        return f"Asset {self.id} for {self.campaign.id}"


class AdPayment(models.Model):
    campaign = models.ForeignKey(AdCampaign, on_delete=models.CASCADE, related_name='payments')
    paymentProvider = models.TextField()
    transactionId = models.CharField(max_length=100, unique=True, default=uuid.uuid4,null=True,blank=True)
    paymentReference = models.TextField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.ForeignKey(AdPaymentStatus, on_delete=models.PROTECT)
    paidAt = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payment {self.id} ({self.status.code})"


class AdPersona(models.Model):
    campaign = models.ForeignKey(AdCampaign, on_delete=models.CASCADE, related_name='personas')
    gender = models.CharField(max_length=50, blank=True, null=True)
    categories = models.ManyToManyField('app_ib.BusinessCategory', blank=True)
    ageBetween = models.CharField(max_length=50, blank=True, null=True)
    personaType = models.CharField(max_length=50, blank=True, null=True)
    segment = models.ForeignKey('app_ib.BusinessSegment', on_delete=models.PROTECT, blank=True, null=True)


    def __str__(self):
        return f"Persona {self.id}  for ({self.campaign.title or 'Untitled'})"

class AdStatEvent(models.Model):
    campaign = models.ForeignKey(AdCampaign, on_delete=models.CASCADE, related_name='events')
    eventType = models.ForeignKey(AdEventType, on_delete=models.PROTECT)
    userSessionId = models.CharField(max_length=255, blank=True, null=True)
    metadata = models.JSONField(default=dict)
    createdAt = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['campaign', 'eventType']),
        ]

    def __str__(self):
        return f"{self.eventType.code} - {self.campaign.id}"


class AdStatAggregate(models.Model):
    campaign = models.ForeignKey(AdCampaign, on_delete=models.CASCADE, related_name='aggregates')
    date = models.DateField()
    impressions = models.IntegerField(default=0)
    clicks = models.IntegerField(default=0)
    formSubmissions = models.IntegerField(default=0)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('campaign', 'date')

    def __str__(self):
        return f"Aggregate for {self.campaign.id} on {self.date}"


# ===== HOME HERO BANNER TABLES (additive — home-page hero carousel slides) =====
#
# WHY these live in the ads module: hero slides are first-party promotional
# placements — editorially managed marketing surfaces, exactly like ad
# placements — so they belong with the advertising domain rather than the
# core app_ib catalog models.
#
# SCALABILITY / ARCHITECTURE NOTES (read before extending):
# - Buttons and metrics are SEPARATE tables (BannerButton / BannerMetric)
#   instead of JSON blobs or inline columns on the banner. This keeps them
#   queryable, individually editable in admin (inlines), and reusable: any
#   future banner-like model (e.g. a CategoryPageBanner or SeasonalBanner)
#   can reuse these tables by ADDING a new nullable FK column to them —
#   never by renaming/removing the existing `banner` FK. Additive only.
# - Buttons are OPTIONAL and variable count: the frontend renders 0–2 of
#   them (the `isPrimary` one gets the highlighted CTA styling).
# - Metrics carry their own `index` so editors control on-slide ordering
#   without re-creating rows.
# - The M2M to app_ib.Business is intentionally OPTIONAL: when a banner has
#   fewer than 2 businesses assigned, the engine endpoint backfills with the
#   top `trendingScore` businesses so the slide's business cards never
#   render empty. Editors only curate when they want to.


# Which front-end page a banner belongs to. Lets one editor-managed table feed
# every page's hero carousel; the controller filters by this and the frontend
# requests its own page's banners. Add a new key here when a new page wants
# admin-managed banners — no schema change needed beyond extending this list.
BANNER_PAGE_CHOICES = [
    ("home", "Home"),
    ("architects", "Architects"),
    ("shops", "Shops"),
    ("products", "Products"),
    ("businesses", "Businesses"),
    ("catalogues", "Catalogues"),
    ("about", "About"),
    ("blog", "Blog"),
    ("explore", "Explore"),
    ("contact", "Contact"),
]
BANNER_PAGE_DEFAULT = "home"

# Which signed-in cohort a slide targets. 'all' = everyone (incl. anon);
# 'buyers' = signed-in users who don't own a business; 'sellers' = users who
# own a Business. HomeBannerController filters slides by the requester's bucket.
BANNER_AUDIENCE_CHOICES = [
    ("all", "Everyone"),
    ("buyers", "Signed-in buyers"),
    ("sellers", "Business owners"),
]
BANNER_AUDIENCE_DEFAULT = "all"


class HomeHeroBanner(models.Model):
    """One slide of a page's hero carousel.

    Despite the legacy name this table now backs EVERY page's hero (filtered by
    `page`), not just home — the model name is kept to avoid a table rename.

    Background is EITHER a CSS gradient string (or a frontend theme key such
    as 'green'/'amber'/'navy'/'plum') OR an image URL — both are stored so a
    slide can carry a gradient with an optional image overlay; the frontend
    decides how to render whichever is present.
    """
    # Page this slide renders on. Existing rows default to "home" so the home
    # carousel is unaffected by this column being added.
    page = models.CharField(max_length=40, choices=BANNER_PAGE_CHOICES,
                            default=BANNER_PAGE_DEFAULT, db_index=True)
    tag = models.CharField(max_length=100)                                  # eyebrow text above the title
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    backgroundGradient = models.CharField(max_length=255, blank=True, default='')  # CSS gradient OR theme key
    backgroundImageUrl = models.TextField(blank=True, default='')                  # optional background image
    displayOrder = models.PositiveIntegerField(default=0, db_index=True)    # carousel position (asc)
    isActive = models.BooleanField(default=True)                            # soft on/off switch for editors
    # Cohort this slide targets (all/buyers/sellers) — filtered per requester.
    audience = models.CharField(max_length=10, choices=BANNER_AUDIENCE_CHOICES,
                                default=BANNER_AUDIENCE_DEFAULT, db_index=True)
    # Optional scheduling window — both nullable so an evergreen banner needs no dates.
    startsAt = models.DateTimeField(null=True, blank=True)
    endsAt = models.DateTimeField(null=True, blank=True)
    # Up to 2 businesses are RENDERED per slide; more may be assigned, the
    # endpoint takes the first 2 (stable id order) and backfills if short.
    businesses = models.ManyToManyField('app_ib.Business', blank=True, related_name='heroBanners')
    createdAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['displayOrder', 'id']
        verbose_name = "Home Hero Banner"
        verbose_name_plural = "Home Hero Banners"

    def __str__(self):
        return f"Hero Banner {self.pk}: {self.title}"


class BannerButton(models.Model):
    """A CTA button on a banner. 0–2 are rendered per slide.

    `isPrimary=True` marks the main CTA (the frontend already has dedicated
    emphasized CSS for it); `isPrimary=False` renders as the normal/ghost
    button. `link` is optional — a button without a link falls back to the
    frontend's default enquiry flow.

    Reuse note: future banner-like models should reuse THIS table by adding
    their own nullable FK alongside `banner` (additive-only schema policy).
    """
    banner = models.ForeignKey(HomeHeroBanner, on_delete=models.CASCADE, related_name='buttons')
    label = models.CharField(max_length=100)
    link = models.TextField(blank=True, default='')   # internal path (e.g. /v3/plans) or absolute URL
    isPrimary = models.BooleanField(default=False)

    class Meta:
        ordering = ['-isPrimary', 'id']  # primary CTA first, then insertion order
        verbose_name = "Banner Button"
        verbose_name_plural = "Banner Buttons"

    def __str__(self):
        kind = "primary" if self.isPrimary else "secondary"
        return f"{self.label} ({kind}) on banner {self.banner_id}"


class BannerMetric(models.Model):
    """One of the (typically 3) stat figures on a banner slide.

    `metric` is the headline value text (e.g. "500+", "4.8 ★"), `description`
    the small label under it, and `index` the editor-controlled display order.

    Reuse note: same additive FK strategy as BannerButton — future banner-like
    models add their own nullable FK here rather than duplicating the table.
    """
    banner = models.ForeignKey(HomeHeroBanner, on_delete=models.CASCADE, related_name='metrics')
    metric = models.CharField(max_length=50)         # the value text shown big
    description = models.CharField(max_length=150)   # the small label under the value
    index = models.PositiveSmallIntegerField(default=0)  # display order on the slide (asc)

    class Meta:
        ordering = ['index', 'id']
        verbose_name = "Banner Metric"
        verbose_name_plural = "Banner Metrics"

    def __str__(self):
        return f"{self.metric} — {self.description} (banner {self.banner_id})"
