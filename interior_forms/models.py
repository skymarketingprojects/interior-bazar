"""
Backend-controlled definitions for the public lead-creating forms.

The SPA renders these forms from the JSON stored here (fields, colours, help
text, validation, payload mapping) instead of hard-coding them. Submission
endpoints are untouched — the schema's `submit` block only tells the frontend
WHERE to post and how to map field ids onto the existing payload shape.
Canonical schema shape is documented in interior_forms/SCHEMA.md.
"""
from django.db import models


class FormDefinition(models.Model):
    # slug the frontend fetches by: enquiry-wizard, catalogue-download,
    # match-wizard, contact-v3, ads-query
    key = models.SlugField(max_length=64, unique=True)
    # where the form lives, for admin readability only
    page = models.CharField(max_length=255, blank=True, default='')
    component = models.CharField(max_length=255, blank=True, default='')
    # full form schema — see SCHEMA.md for the canonical shape
    schema = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    version = models.IntegerField(default=1)
    createdOn = models.DateTimeField(auto_now_add=True)
    updatedOn = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['key']

    def __str__(self):
        return f"{self.key} (v{self.version}{'' if self.is_active else ', inactive'})"
