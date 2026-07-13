"""interior_cms/models.py — site content / CMS domain.

Moved out of app_ib (TASK 16, state-only move — db_table names pinned so the
tables are untouched). These are marketing/site-content models, not core:
Blog, Pages/Page/Section, QNA, OfferText/OfferHeading, StockMedia,
NewsletterSubscriber, OurClients, ReelSection, and TeamMember (About-page
people — moved out of app_ib.engine_models). The CustomUser FK stays a
cross-app string ref to app_ib (until later). The dead Banners/Constants
tables were deleted, not moved (nothing read them).
"""
from django.db import models
from django_quill.fields import QuillField

from app_ib.Utils.ModelHelper import indexShifting
from app_ib.Utils.MyMethods import MY_METHODS


class Blog(models.Model):
    user = models.ForeignKey('app_ib.CustomUser', on_delete=models.CASCADE, null=True, blank=True)
    title = models.TextField()
    slug = models.CharField(max_length=800, unique=True, null=True, blank=True)
    cover = models.FileField(null=True, blank=True, upload_to='blog/cover')
    coverImageUrl = models.TextField(default='', null=True, blank=True)
    description = QuillField(null=True, blank=True)
    author = models.TextField()
    authorImageUrl = models.URLField(default='', null=True, blank=True)
    isFeatured = models.BooleanField(default=False)
    featuredOrder = models.PositiveIntegerField(default=0)
    metaTitle = models.CharField(max_length=300, blank=True, default='')
    metaDescription = models.TextField(blank=True, default='')
    focusKeyword = models.CharField(max_length=200, blank=True, default='')
    status = models.CharField(max_length=10, choices=(('draft', 'draft'), ('published', 'published')), default='draft')
    timestamp = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'author {self.author} title:{self.title} timestamp:{self.timestamp}'

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            self.slug = MY_METHODS.generate_slug(self.title)
        super().save(*args, **kwargs)

    class Meta:
        db_table = "app_ib_blog"


class NewsletterSubscriber(models.Model):
    """Email newsletter subscribers — sourced from blog / landing pages."""
    email = models.EmailField(unique=True)
    user = models.ForeignKey('app_ib.CustomUser', null=True, blank=True, on_delete=models.SET_NULL, related_name="newsletter_subs")
    source = models.CharField(max_length=30, default="blog")
    isConfirmed = models.BooleanField(default=False)
    isActive = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"NewsletterSubscriber {self.email} (confirmed={self.isConfirmed})"

    class Meta:
        db_table = "app_ib_newslettersubscriber"


class OfferHeading(models.Model):
    title = models.TextField()
    isActive = models.BooleanField(default=False)

    def __str__(self):
        return f' pk {self.pk} title:{self.title}'

    class Meta:
        db_table = "app_ib_offerheading"


class Pages(models.Model):
    pageName = models.CharField(max_length=500, unique=True)
    title = models.CharField(max_length=500)
    content = QuillField(null=True, blank=True)

    def __str__(self):
        return f'page_name: {self.pageName} title:{self.title}'

    class Meta:
        db_table = "app_ib_pages"
        verbose_name_plural = "information pages"


class QNA(models.Model):
    question = models.TextField()
    answer = models.TextField()
    isActive = models.BooleanField(default=False)

    def __str__(self):
        return f' pk {self.pk} question:{self.question}'

    class Meta:
        db_table = "app_ib_qna"


class Page(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"Page {self.name}"

    class Meta:
        db_table = "app_ib_page"
        verbose_name_plural = "stockimages page"


class Section(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"Section {self.name}"

    class Meta:
        db_table = "app_ib_section"


class StockMedia(models.Model):
    image = models.URLField(max_length=2250, null=True, blank=True)
    video = models.URLField(max_length=2250, null=True, blank=True)
    page = models.ForeignKey(Page, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True)
    index = models.IntegerField(default=1)

    def __str__(self):
        if self.page and self.section:
            return f"StockMedia {self.pk} | Page: {self.page.name} | Section: {self.section.name} | Index: {self.index}"
        elif self.page:
            return f"StockMedia {self.pk} | Page: {self.page.name} | Index: {self.index}"
        elif self.section:
            return f"StockMedia {self.pk} | Section: {self.section.name} | Index: {self.index}"
        return f"StockMedia {self.pk} | Index: {self.index}"

    class Meta:
        db_table = "app_ib_stockmedia"


class OfferText(models.Model):
    text = QuillField(null=True, blank=True)
    link = models.URLField(max_length=2250, null=True, blank=True)
    color = models.CharField(max_length=100, default='', null=True, blank=True)
    show = models.BooleanField(default=False)

    def __str__(self):
        return f' pk {self.pk} text:{self.text}'

    class Meta:
        db_table = "app_ib_offertext"


class OurClients(models.Model):
    image = models.URLField(max_length=2250)
    name = models.CharField(max_length=2250)
    index = models.IntegerField(default=1, null=True, blank=True)

    def __str__(self):
        return f' pk {self.pk} name:{self.name}'

    def save(self, *args, **kwargs):
        if not self.index:
            self.index = self.__class__.objects.all().count() + 1
        indexShifting(instance=self, filter_attr='index')
        super().save(*args, **kwargs)

    class Meta:
        db_table = "app_ib_ourclients"


class ReelSection(models.Model):
    video = models.URLField(max_length=2250)
    name = models.CharField(max_length=2250)
    index = models.IntegerField(default=1, null=True, blank=True)

    def __str__(self):
        return f' pk {self.pk} name:{self.name}'

    def save(self, *args, **kwargs):
        if not self.index:
            self.index = self.__class__.objects.all().count() + 1
        indexShifting(instance=self, filter_attr='index')
        super().save(*args, **kwargs)

    class Meta:
        db_table = "app_ib_reelsection"


class TeamMember(models.Model):
    """An About-page team member (task 77) — admin-editable; the real people shown
    on the About page will change over time. `isPlaceholder` marks the non-person
    "We're hiring" tile."""
    name = models.CharField(max_length=120)
    role = models.CharField(max_length=120, blank=True, default="")
    initials = models.CharField(max_length=6, blank=True, default="")
    gradient = models.CharField(max_length=200, blank=True, default="")  # avatar chip fill when no photo
    photoUrl = models.TextField(blank=True, default="")
    bio = models.TextField(blank=True, default="")
    isPlaceholder = models.BooleanField(default=False)  # the "join us / we're hiring" tile
    displayOrder = models.PositiveIntegerField(default=0, db_index=True)
    isActive = models.BooleanField(default=True)

    class Meta:
        db_table = "app_ib_teammember"
        ordering = ["displayOrder", "id"]

    def __str__(self):
        return f"{self.name} ({self.role})"
