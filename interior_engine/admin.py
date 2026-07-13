from django.contrib import admin
from django.apps import apps
from django.contrib.admin.sites import AlreadyRegistered

# Auto-register every model this app owns (same pattern as app_ib/admin.py). A model
# that already has a curated ModelAdmin registered elsewhere (app_ib registers the
# rich engine admins) raises AlreadyRegistered and is skipped, so that one wins.
for _model in apps.get_app_config("interior_engine").get_models():
    try:
        admin.site.register(_model)
    except AlreadyRegistered:
        pass
