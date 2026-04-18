from django.db import models
from django.conf import settings

class Access(models.Model):
    permissionName = models.CharField(max_length=255, unique=True)
    permission= models.BooleanField(default=False)

    def __str__(self):
        return self.permissionName


class Role(models.Model):
    name = models.CharField(max_length=255, unique=True)
    is_full_access = models.BooleanField(default=False)
    access = models.ManyToManyField(Access, related_name="roles", blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="roles", blank=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def can_delete(self):
        """
        Role cannot be deleted if any user is assigned
        """
        return not self.users.exists()

    def __str__(self):
        return self.name

class UserCreationAudit(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_user_record")
    createdBy = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,null=True, related_name="created_users")
    createdAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "User Creation Audit"
        verbose_name_plural = "User Creation Audits"

    def __str__(self):
        return f"{self.user.username} created by {self.createdBy.username if self.createdBy else 'system'}"
