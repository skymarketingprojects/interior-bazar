"""app_ib chat models — human buyer↔seller conversation threads + messages.
Created from a lead; independent little domain kept in app_ib (TASK 17)."""
from django.db import models
from django.conf import settings
from app_ib.Utils.EngineConfig import CONVERSATION_STATUS

USER = settings.AUTH_USER_MODEL


class Conversation(models.Model):
    """A chat thread between a client and a business (owner). Created from a lead."""
    lead = models.ForeignKey("interior_leads.LeadQuery", null=True, blank=True, on_delete=models.SET_NULL,
                             related_name="conversations")
    business = models.ForeignKey("interior_business.Business", null=True, blank=True, on_delete=models.SET_NULL,
                                 related_name="conversations")
    clientUser = models.ForeignKey(USER, null=True, on_delete=models.SET_NULL, related_name="client_conversations")
    businessUser = models.ForeignKey(USER, null=True, on_delete=models.SET_NULL, related_name="business_conversations")
    status = models.CharField(max_length=20, default=CONVERSATION_STATUS.REQUESTED)
    declineReason = models.CharField(max_length=255, blank=True, default="")
    lastMessageAt = models.DateTimeField(null=True, blank=True, db_index=True)
    # item 6: first-response tracking — set on first business-side reply
    firstResponseSeconds = models.PositiveIntegerField(null=True, blank=True)
    # Per-participant soft delete: hides the thread from that user's list only
    # (task 53 — "Delete enquiry"). The conversation is never hard-deleted so the
    # other party keeps their copy.
    clientDeleted = models.BooleanField(default=False)
    businessDeleted = models.BooleanField(default=False)
    # Attached label ids (buyer inbox organisation, task 54) — e.g. ["l_vip","l_hot"].
    labels = models.JSONField(default=list, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "app_ib_conversation"
        app_label = "app_ib"
        indexes = [models.Index(fields=["clientUser", "status"]),
                   models.Index(fields=["businessUser", "status"])]

    def other_party(self, user_id):
        return self.businessUser_id if user_id == self.clientUser_id else self.clientUser_id

    def is_participant(self, user_id):
        return user_id in (self.clientUser_id, self.businessUser_id)

    def __str__(self):
        return f"Conversation {self.pk} [{self.status}]"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(USER, null=True, on_delete=models.SET_NULL, related_name="sent_messages")
    body = models.TextField()
    # Uploaded file attachments — list of {name, url, size} (task 56).
    attachments = models.JSONField(default=list, blank=True)
    isRead = models.BooleanField(default=False)
    createdAt = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "app_ib_message"
        app_label = "app_ib"
        indexes = [models.Index(fields=["conversation", "createdAt"])]
