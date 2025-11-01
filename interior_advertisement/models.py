import uuid
from django.db import models
from django.utils import timezone
from decimal import Decimal


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

    def __str__(self):
        return f"{self.title or 'Untitled'} ({self.status.code})"


class AdAsset(models.Model):
    campaign = models.ForeignKey(AdCampaign, on_delete=models.CASCADE, related_name='assets')
    assetType = models.ForeignKey(AdAssetType, on_delete=models.PROTECT)
    s3Key = models.TextField()
    meta = models.JSONField(default=dict)

    def __str__(self):
        return f"Asset {self.id} for {self.campaign.id}"


class AdPayment(models.Model):
    campaign = models.ForeignKey(AdCampaign, on_delete=models.CASCADE, related_name='payments')
    paymentProvider = models.TextField()
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
        return f"Aggregate for {self.campaign_id} on {self.date}"
