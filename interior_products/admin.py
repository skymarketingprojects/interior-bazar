from django.contrib import admin
from django.apps import apps
from django.contrib.admin.sites import AlreadyRegistered

from interior_products.models import Catelogue, CatelogueImage


class CatelogueImageInline(admin.TabularInline):
    model = CatelogueImage
    extra = 1


@admin.register(Catelogue)
class CatelogueAdmin(admin.ModelAdmin):
    """Explicit admin so staff can fill the description + specifications (JSON)
    that the catalogue-detail Description/Specifications tabs read, and manage
    the catalogue's images inline."""
    list_display = ("id", "title", "business", "catelogueType", "isActive")
    list_filter = ("catelogueType", "isActive")
    search_fields = ("title", "description")
    inlines = [CatelogueImageInline]


# Auto-register every other app model. Catelogue is registered explicitly above;
# the AlreadyRegistered guard skips it here.
app_models = apps.get_app_config("interior_products").get_models()

for model in app_models:
    try:
        admin.site.register(model)
    except AlreadyRegistered:
        pass