from django.db import models
from django.conf import settings
from datetime import datetime
from app_ib.Utils.Names import NAMES

class GMBBusiness(models.Model):
    businessName = models.CharField(max_length=500)
    rating = models.CharField(max_length=50, help_text="Store in format 4.8(32)")
    ratingValue = models.FloatField(default=0.0)
    reviewCount = models.IntegerField(default=0)
    address = models.TextField(null=True, blank=True)
    phone = models.CharField(max_length=100, null=True, blank=True)
    web = models.URLField(max_length=500, null=True, blank=True)
    mapLink = models.URLField(max_length=500, null=True, blank=True)
    socialLinks = models.JSONField(default=list, null=True, blank=True)
    waMessage = models.URLField(max_length=500, null=True, blank=True)
    assignedUser = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_gmb_leads')
    rankingRate = models.FloatField(default=0.0)
    tier = models.CharField(max_length=1, null=True, blank=True)
    platform = models.CharField(max_length=100, default=NAMES.DEFAULT_PLATFORM)
    remark = models.TextField(null=True, blank=True)
    category = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=50, default='New')
    state = models.CharField(max_length=100, null=True, blank=True)
    
    logs = models.JSONField(default=list, null=True, blank=True)
    
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._initial_state = self._get_log_state()

    def _get_log_state(self):
        return {
            NAMES.ASSIGNED_USER: self.assignedUser.username if self.assignedUser else None,
            NAMES.RANKING_RATE: self.rankingRate,
            NAMES.REMARK: self.remark,
            NAMES.TIER: self.tier,
            NAMES.STATUS_KEY: self.status,
            NAMES.STATE: self.state,
            NAMES.ADDRESS: self.address,
            NAMES.PHONE: self.phone
        }


    def save(self, *args, **kwargs):
        is_new = self.pk is None
        current_state = self._get_log_state()
        events = []

        if is_new:
            events.append(NAMES.GMB_LEAD_CREATED)
        else:
            for field, old_val in self._initial_state.items():
                new_val = current_state[field]
                if old_val != new_val:
                    events.append(f"{field} updated from '{old_val}' to '{new_val}'")

        if events:
            if not isinstance(self.logs, list):
                self.logs = []
            
            # If triggered_by is available as a temporary attribute (set by controller)
            triggered_by_username = NAMES.SYSTEM_USER
            if hasattr(self, '_triggered_by') and self._triggered_by:
                triggered_by_username = self._triggered_by.username

            self.logs.append({
                NAMES.EVENT: ", ".join(events),
                NAMES.TIMESTAMP: datetime.now().strftime(NAMES.DMY_12M),
                NAMES.TRIGGERED_BY: triggered_by_username
            })

        super().save(*args, **kwargs)
        self._initial_state = current_state

    def __str__(self):
        return self.businessName

    class Meta:
        verbose_name = "GMB Business"
        verbose_name_plural = "GMB Businesses"


class GMBActivityLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    business = models.ForeignKey(GMBBusiness, on_delete=models.CASCADE, related_name='activity_logs')
    field_changed = models.CharField(max_length=255)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)
    triggered_by = models.CharField(max_length=100, default=NAMES.SYSTEM_USER)

    def __str__(self):
        return f"{self.business.businessName} - {self.field_changed} at {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']


class AdminAuditLog(models.Model):
    """Append-only audit trail for the v3 admin ops console. Every level-3
    (sensitive) action appends one row via append_audit()
    (interior_admin/Controllers/Audit/AuditController.py). Feeds the `audit`
    module (GET /api/v1/admin/audit/). Not updated or deleted in normal flow."""
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_audit_entries')
    role = models.CharField(max_length=100, null=True, blank=True)
    action = models.CharField(max_length=255)
    moduleKey = models.CharField(max_length=100, db_index=True)
    detail = models.TextField(null=True, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"{self.moduleKey}:{self.action} by {self.actor_id} @ {self.createdAt}"

    class Meta:
        ordering = ['-createdAt']
        verbose_name = "Admin Audit Log"


class NotificationTemplate(models.Model):
    """Editable notification templates for the admin `templates` module
    (promptsadmin task 48). The delivery system renders channel messages from
    these by `key`. `variables` lists the placeholder names available to body."""
    key = models.CharField(max_length=150, unique=True)
    name = models.CharField(max_length=200, default='', blank=True)  # human-friendly label
    channel = models.CharField(max_length=50, default='email')  # email | sms | whatsapp | push | inapp
    # DLT/TRAI-registered template id — required for India SMS delivery (sms channel).
    dltId = models.CharField(max_length=100, default='', blank=True)
    subject = models.CharField(max_length=300, default='', blank=True)
    body = models.TextField(default='', blank=True)
    variables = models.JSONField(default=list, blank=True)
    active = models.BooleanField(default=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.key} ({self.channel})"

    class Meta:
        ordering = ['key']


class AdminModuleAccess(models.Model):
    """One (role, module) → permission-level cell of the admin RBAC matrix
    (promptsadmin task 55). Level: 0 none / 1 read / 2 write / 3 sensitive.
    Keyed to the existing rbac_module.Role so is_full_access + user assignment
    keep working; super_admin (is_full_access) short-circuits to 3 everywhere."""
    role = models.ForeignKey('rbac_module.Role', on_delete=models.CASCADE, related_name='module_access')
    moduleKey = models.CharField(max_length=100, db_index=True)
    level = models.PositiveSmallIntegerField(default=0)  # 0..3

    def __str__(self):
        return f"{self.role_id}:{self.moduleKey}={self.level}"

    class Meta:
        unique_together = ('role', 'moduleKey')


class ListingReport(models.Model):
    """User-submitted report against a business/listing for the admin `reports`
    module (promptsadmin task 54). Generic target (targetType+targetId) to avoid
    coupling to a single model. Public submit; admin resolve."""
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='listing_reports')
    reporterEmail = models.EmailField(blank=True, default='')
    targetType = models.CharField(max_length=50, default='business')  # business | listing | product
    targetId = models.CharField(max_length=100, default='', blank=True)
    reason = models.TextField()
    status = models.CharField(max_length=20, default='open')          # open | resolved | dismissed
    resolver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports_resolved')
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Report #{self.pk} {self.targetType}:{self.targetId} ({self.status})"

    class Meta:
        ordering = ['-createdAt']


class Testimonial(models.Model):
    """Customer testimonial for the admin `testimonials` module (promptsadmin
    task 53) and the marketing site's public read. Distinct from Feedback/Review."""
    author = models.CharField(max_length=200)
    role = models.CharField(max_length=200, default='', blank=True)   # e.g. "Founder, XYZ Interiors"
    quote = models.TextField()
    type = models.CharField(max_length=50, default='text')           # text | video | banner
    featured = models.BooleanField(default=False)                    # banner/featured placement
    status = models.CharField(max_length=20, default='active')       # active | hidden (UI: Published/Hidden)
    avatarUrl = models.URLField(max_length=1000, default='', blank=True)
    # task 20: explicit display order + video/rating/business metadata.
    index = models.IntegerField(default=0, db_index=True)
    videoUrl = models.URLField(max_length=1000, default='', blank=True)  # full YouTube/other link
    rating = models.FloatField(null=True, blank=True)
    businessName = models.CharField(max_length=200, default='', blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.author}: {self.quote[:40]}"

    class Meta:
        ordering = ['index']


class Expense(models.Model):
    """Operating expense line for the admin `revenue` module (promptsadmin task
    52). Feeds unit-economics aggregation alongside real payment revenue."""
    KIND_CHOICES = [('fixed', 'Fixed'), ('reinvestment', 'Reinvestment')]
    label = models.CharField(max_length=300)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    category = models.CharField(max_length=100, default='', blank=True)
    # Split for the P&L waterfall (task 17): fixed opex vs growth reinvestment.
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default='fixed')
    incurredAt = models.DateField(null=True, blank=True)
    createdBy = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses_added')
    createdAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.label}: {self.amount}"

    class Meta:
        ordering = ['-incurredAt', '-createdAt']


class RevenueAssumption(models.Model):
    """Singleton (id=1) of admin-tunable unit-economics assumptions (task 17), so
    LTV / CAC / payback are transparent inputs rather than invented numbers.
    ponytail: one settings row, not per-value tables."""
    avgLifetimeMonths = models.PositiveIntegerField(default=18)
    grossMargin = models.DecimalField(max_digits=4, decimal_places=2, default=0.70)  # 0..1
    revenueTarget = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    newCustomersThisMonth = models.PositiveIntegerField(default=0)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"assumptions(lifetime={self.avgLifetimeMonths}mo margin={self.grossMargin})"


class QualificationWeightConfig(models.Model):
    """Singleton signal→weight config for lead qualification (admin `weights`
    module, promptsadmin task 51). The qualification pipeline reads row id=1.
    Writes are super-admin only, level-3 (audited)."""
    weights = models.JSONField(default=dict, blank=True)  # {signal_key: weight}
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"QualificationWeightConfig #{self.pk}"


class SlotInventory(models.Model):
    """Priority-slot inventory grid for the admin `slots` module (promptsadmin
    task 50): 12 categories × 6 priority regions. Each cell = one row. Overrides
    (capacity/holder) are level-3 (audited)."""
    category = models.CharField(max_length=150, db_index=True)
    region = models.CharField(max_length=150, db_index=True)
    capacity = models.PositiveIntegerField(default=0)
    holder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='held_slots')
    priority = models.PositiveIntegerField(default=0)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.category}/{self.region} cap={self.capacity}"

    class Meta:
        ordering = ['category', 'region']
        unique_together = ('category', 'region')


class BrandAsset(models.Model):
    """Singleton brand assets for the admin `brand-logo` module (promptsadmin
    task 49). Stores S3 URLs uploaded client-side (same pattern as the rest of
    the app's images). Row id=1 is the live brand. Level-3 (audited) on write."""
    logoUrl = models.URLField(max_length=1000, default='', blank=True)
    faviconUrl = models.URLField(max_length=1000, default='', blank=True)
    tagline = models.CharField(max_length=200, default='', blank=True)  # default brand tagline
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"BrandAsset #{self.pk}"


class BrandLogo(models.Model):
    """A scheduled brand logo (seasonal/campaign) for the `brand-logo` module
    (task 27). The public resolver picks today's active one by date window;
    BrandAsset(id=1) is the always-on default fallback.
    ponytail: FIXED calendar dates (YYYY-MM-DD), not recurring month-day — a
    "Diwali 2027" entry is added yearly. Recurring windows are a future option."""
    label = models.CharField(max_length=200, default='', blank=True)
    imageUrl = models.URLField(max_length=1000)
    tagline = models.CharField(max_length=200, default='', blank=True)
    activeFrom = models.DateField(null=True, blank=True)   # null → open start (always-on if activeTo also null)
    activeTo = models.DateField(null=True, blank=True)     # null → open end
    createdAt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"BrandLogo #{self.pk} {self.label}"

    class Meta:
        ordering = ['-activeFrom', '-createdAt']
