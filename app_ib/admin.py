from django.contrib import admin
from django.apps import apps
from django.contrib.admin.sites import AlreadyRegistered

# Register your models here.
from app_ib import models
from app_ib.engine_models import (
    Award, ProcessStep, UserSession, RelatedItem,
    BusinessSpecialization, SpecializationJob, Testimonial, Differentiator,
    JoinUsCta, JoinUsStep, ShopUpdate, ShopQuestion, ShopImage,
)


class JoinUsStepInline(admin.TabularInline):
    model = JoinUsStep
    extra = 1
    ordering = ("index", "id")


@admin.register(JoinUsCta)
class JoinUsCtaAdmin(admin.ModelAdmin):
    """Home 'Join us' final CTA band (served by home/join-us/). Buttons store a
    label + a HomeCtaAction dict e.g. {"kind":"route","to":"PLANS_V3"}. The ordered
    'how matching works' steps are edited inline (variable count)."""
    list_display = ("titleLead", "titleAccent", "isActive", "index", "timestamp")
    list_filter = ("isActive",)
    inlines = [JoinUsStepInline]


@admin.register(Differentiator)
class DifferentiatorAdmin(admin.ModelAdmin):
    """'What makes IB different' cards (served by home/differentiators/).
    `eliminates` is a JSON list of competitor labels shown with strikethrough,
    e.g. ["JustDial — unfiltered volume", "Google Ads — only website traffic"]."""
    list_display = ("heading", "icon", "eliminates_count", "isActive", "index", "timestamp")
    list_filter = ("isActive",)
    search_fields = ("heading", "description")
    ordering = ("index", "id")

    @admin.display(description="# eliminates")
    def eliminates_count(self, obj):
        return len(obj.eliminates or [])
from app_ib.models import NewsletterSubscriber


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    """Admin-entered video + text testimonials for the home 'Video stories'
    section (served by home/testimonials/). Paste an embeddable video link into
    `videoUrl` (any provider — YouTube Shorts, Instagram Reels, etc.) to make it a
    VIDEO testimonial; leave `videoUrl` empty and fill `quote` for a TEXT one."""
    list_display = ("authorName", "businessName", "kind", "rating", "isActive", "index", "timestamp")
    list_filter = ("isActive",)
    search_fields = ("authorName", "businessName", "quote")
    ordering = ("index", "-timestamp")
    fieldsets = (
        (None, {"fields": ("authorName", "authorRole", "businessName", "rating", "isActive", "index")}),
        ("Video testimonial", {
            "fields": ("videoUrl", "thumbnailUrl"),
            "description": "Embeddable video link for ANY provider (YouTube Shorts, "
                           "Instagram Reels, direct MP4, …). Leave empty for a text-only testimonial.",
        }),
        ("Text / caption", {"fields": ("quote",),
                            "description": "Shown as the quote on a text testimonial, or the caption on a video one."}),
    )

    @admin.display(description="Kind")
    def kind(self, obj):
        return "Video" if (obj.videoUrl or "").strip() else "Text"


@admin.register(Award)
class AwardAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "issuer", "year", "business", "shop", "architect", "isActive", "index", "timestamp")
    list_filter = ("kind", "isActive")
    search_fields = ("title", "issuer")
    ordering = ("index", "-timestamp")


@admin.register(ProcessStep)
class ProcessStepAdmin(admin.ModelAdmin):
    list_display = ("stepNumber", "title", "business", "shop", "architect", "isActive", "index", "timestamp")
    list_filter = ("isActive",)
    search_fields = ("title",)
    ordering = ("index", "-timestamp")


@admin.register(ShopUpdate)
class ShopUpdateAdmin(admin.ModelAdmin):
    """Per-shop 'Shop updates' cards (served by shop/<id|slug>/). `badge` is a short
    label e.g. "New"/"Offer"; `color` is an optional CSS gradient/colour."""
    list_display = ("title", "shop", "badge", "displayOrder", "isActive", "timestamp")
    list_filter = ("isActive",)
    search_fields = ("title", "body", "shop__name")
    ordering = ("displayOrder", "-timestamp")


@admin.register(ShopQuestion)
class ShopQuestionAdmin(admin.ModelAdmin):
    """Per-shop customer Q&A entries (served by shop/<id|slug>/). `answer` is
    optional until the shop responds; `askedBy` is a short display name."""
    list_display = ("question", "shop", "askedBy", "displayOrder", "isActive", "timestamp")
    list_filter = ("isActive",)
    search_fields = ("question", "answer", "shop__name")
    ordering = ("displayOrder", "-timestamp")


@admin.register(ShopImage)
class ShopImageAdmin(admin.ModelAdmin):
    """Per-shop gallery images (served by shop/<id|slug>/). Shown in the preview
    sidebar hero carousel + full-details 'Photos' tab; falls back to
    coverImage/bannerImage when empty."""
    list_display = ("shop", "index", "imageUrl", "isActive", "timestamp")
    list_filter = ("isActive",)
    search_fields = ("shop__name", "imageUrl")
    ordering = ("index", "timestamp")


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "jti", "deviceLabel", "ipAddress", "city", "lastActiveAt", "createdAt", "revokedAt")
    list_filter = ("revokedAt",)
    search_fields = ("user__username", "jti", "deviceLabel", "ipAddress")
    ordering = ("-lastActiveAt",)


@admin.register(RelatedItem)
class RelatedItemAdmin(admin.ModelAdmin):
    list_display = ("sourceContentType", "sourceObjectId", "targetContentType", "targetObjectId", "score", "reason", "updatedAt")
    list_filter = ("reason", "sourceContentType")
    ordering = ("-score",)


@admin.register(BusinessSpecialization)
class BusinessSpecializationAdmin(admin.ModelAdmin):
    list_display = ("business", "source", "snapshotHash", "generatedAt")
    search_fields = ("business__businessName",)
    ordering = ("-generatedAt",)


@admin.register(SpecializationJob)
class SpecializationJobAdmin(admin.ModelAdmin):
    list_display = ("business", "status", "scheduledAt", "reason", "attempts", "updatedAt")
    list_filter = ("status", "entityType")
    search_fields = ("business__businessName",)
    ordering = ("-scheduledAt",)


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "user", "source", "isConfirmed", "isActive", "timestamp")
    list_filter = ("isConfirmed", "isActive", "source")
    search_fields = ("email",)
    ordering = ("-timestamp",)


@admin.register(models.Pages)
class PagesAdmin(admin.ModelAdmin):
    list_display = ("pageName", "title")
    search_fields = ("pageName", "title")


@admin.register(models.QNA)
class QNAAdmin(admin.ModelAdmin):
    list_display = ("question", "isActive")
    search_fields = ("question", "answer")


# admin.site.register(models.Contact)
# admin.site.register(models.CustomUser)
# admin.site.register(models.UserProfile)
# admin.site.register(models.Business)
# admin.site.register(models.BusinessProfile)
# admin.site.register(models.Location)
# admin.site.register(models.Subscription)
# admin.site.register(models.BusinessPlan)
# admin.site.register(models.LeadQuery)
# admin.site.register(models.Quate)
# admin.site.register(models.PlanQuery)
# admin.site.register(models.Feedback)
# admin.site.register(models.Blog)
# admin.site.register(models.Constants)
# admin.site.register(models.Banners)
# admin.site.register(models.OfferHeading)

app_models = apps.get_app_config("app_ib").get_models()

for model in app_models:
    try:
        admin.site.register(model)
    except AlreadyRegistered:
        pass