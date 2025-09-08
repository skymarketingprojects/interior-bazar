from django.contrib import admin
from django.apps import apps
from django.contrib.admin.sites import AlreadyRegistered

# Register your models here.
from app_ib import models

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