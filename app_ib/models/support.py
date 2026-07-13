"""app_ib support/help models — support config singleton, help-centre content
(FAQ/topics/tutorials) and user support tickets (TASK 17)."""
from django.db import models
from django.conf import settings

USER = settings.AUTH_USER_MODEL


class SupportConfig(models.Model):
    """Single source of truth for support/contact channels (task 75) — editable in
    admin, consumed by Contact, Help ("Talk to a human"), About and the legal contact
    boxes. A singleton: only the first row is served. Empty fields (e.g. tollFree)
    render nothing rather than a fabricated placeholder number."""
    supportEmail = models.EmailField(default="help@interiorbazzar.com")
    phone = models.CharField(max_length=30, blank=True, default="")        # display, e.g. +91 88823 14255
    whatsapp = models.CharField(max_length=30, blank=True, default="")     # digits for wa.me, e.g. 918920898168
    tollFree = models.CharField(max_length=30, blank=True, default="")
    officeAddress = models.TextField(blank=True, default="")
    hours = models.CharField(max_length=160, blank=True, default="")
    liveChatAvailable = models.BooleanField(default=False)
    agentCount = models.PositiveIntegerField(default=0)                    # only meaningful if live chat is real
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "app_ib_supportconfig"
        app_label = "app_ib"
        verbose_name = "Support Config"
        verbose_name_plural = "Support Config"

    def __str__(self):
        return "Support Config"


class HelpFaq(models.Model):
    """A help-centre FAQ (task 76) — admin-editable, replaces the static list."""
    question = models.TextField()
    answer = models.TextField()   # may contain <strong> emphasis
    displayOrder = models.PositiveIntegerField(default=0, db_index=True)
    isActive = models.BooleanField(default=True)

    class Meta:
        db_table = "app_ib_helpfaq"
        app_label = "app_ib"
        ordering = ["displayOrder", "id"]

    def __str__(self):
        return self.question[:60]


class HelpTopic(models.Model):
    """A help-centre topic tile (task 76)."""
    title = models.CharField(max_length=120)
    icon = models.CharField(max_length=60, default="ti-help")
    iconBg = models.CharField(max_length=20, default="#e1f5ee")
    iconColor = models.CharField(max_length=20, default="#085041")
    articleCount = models.PositiveIntegerField(default=0)
    displayOrder = models.PositiveIntegerField(default=0, db_index=True)
    isActive = models.BooleanField(default=True)

    class Meta:
        db_table = "app_ib_helptopic"
        app_label = "app_ib"
        ordering = ["displayOrder", "id"]

    def __str__(self):
        return self.title


class HelpTutorial(models.Model):
    """A help-centre video tutorial card (task 76). Gradient is a placeholder thumb
    when no real videoUrl/thumbnail is set."""
    title = models.CharField(max_length=160)
    gradient = models.CharField(max_length=200, blank=True, default="")
    duration = models.CharField(max_length=20, blank=True, default="")
    views = models.CharField(max_length=20, blank=True, default="")
    videoUrl = models.TextField(blank=True, default="")
    displayOrder = models.PositiveIntegerField(default=0, db_index=True)
    isActive = models.BooleanField(default=True)

    class Meta:
        db_table = "app_ib_helptutorial"
        app_label = "app_ib"
        ordering = ["displayOrder", "id"]

    def __str__(self):
        return self.title


class SupportTicket(models.Model):
    """A user-raised support ticket (task 76). Status drives the help "my tickets"
    widget. Anonymous tickets are allowed (user null) as long as an email is given."""
    STATUS_CHOICES = [("open", "Open"), ("in_progress", "In progress"),
                      ("resolved", "Resolved"), ("closed", "Closed")]
    user = models.ForeignKey(USER, null=True, blank=True, on_delete=models.SET_NULL,
                             related_name="support_tickets")
    email = models.EmailField(blank=True, default="")
    subject = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    # Admin support-desk replies (promptsadmin task 47): list of
    # {by, role, body, ts} appended by admin replyTicket. User's original is `message`.
    replies = models.JSONField(default=list, blank=True)
    lastReplyAt = models.DateTimeField(null=True, blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "app_ib_supportticket"
        app_label = "app_ib"
        ordering = ["-createdAt"]

    def __str__(self):
        return f"Ticket #{self.pk} ({self.status}): {self.subject[:40]}"
