from django.contrib import admin
from django.apps import apps
from django.contrib.admin.sites import AlreadyRegistered

# Register your models here.
from app_ib import models
from app_ib.engine_models import Award, ProcessStep, UserSession, RelatedItem
from app_ib.models import NewsletterSubscriber


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


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "user", "source", "isConfirmed", "isActive", "timestamp")
    list_filter = ("isConfirmed", "isActive", "source")
    search_fields = ("email",)
    ordering = ("-timestamp",)


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
# admin.site.register(models.Pages)
# admin.site.register(models.QNA)

app_models = apps.get_app_config("app_ib").get_models()

for model in app_models:
    try:
        admin.site.register(model)
    except AlreadyRegistered:
        pass