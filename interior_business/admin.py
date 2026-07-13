from django.contrib import admin
from django.apps import apps
from django.contrib.admin.sites import AlreadyRegistered

# Auto-register every model this app owns (same pattern as app_ib/admin.py). Any model
# already registered with a curated ModelAdmin elsewhere is skipped via AlreadyRegistered.
for _model in apps.get_app_config("interior_business").get_models():
    try:
        admin.site.register(_model)
    except AlreadyRegistered:
        pass
