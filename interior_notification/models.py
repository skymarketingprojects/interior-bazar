from django.db import models
from django.conf import settings

USER = settings.AUTH_USER_MODEL


class Notification(models.Model):
    """Unread-only store; row deleted on read. Moved here from app_ib.engine_models
    (TASK 17); db_table pinned so the move is state-only (no data touched)."""
    user = models.ForeignKey(USER, on_delete=models.SET_NULL, null=True, related_name="notifications")
    type = models.CharField(max_length=20)
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True, default="")
    actionUrl = models.CharField(max_length=500, blank=True, default="")
    dedupeKey = models.CharField(max_length=255, blank=True, default="")
    groupCount = models.PositiveIntegerField(default=1)
    metadata = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "app_ib_notification"
