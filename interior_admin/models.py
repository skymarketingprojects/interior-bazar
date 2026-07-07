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
    channel = models.CharField(max_length=50, default='email')  # email | sms | whatsapp | push | inapp
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
