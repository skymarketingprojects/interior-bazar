from django.contrib import admin
from django.apps import apps
from django.contrib.admin.sites import AlreadyRegistered

from interior_advertisement.models import HomeHeroBanner, BannerButton, BannerMetric


# ===== HOME HERO BANNER ADMIN (explicit, registered BEFORE the auto-loop) =====
# WHY: non-developers manage hero slides, so buttons and metrics are edited
# inline on the banner page — one screen per slide instead of three separate
# model lists. The auto-register loop below skips these (AlreadyRegistered).


class BannerButtonInline(admin.TabularInline):
    """Edit a slide's CTA buttons in place. Keep to 0–2 rows — the frontend
    renders at most 2 (the isPrimary one gets the emphasized CTA styling)."""
    model = BannerButton
    extra = 0
    max_num = 2


class BannerMetricInline(admin.TabularInline):
    """Edit a slide's stat figures in place. `index` controls on-slide order;
    the home page shows 3 metrics per slide."""
    model = BannerMetric
    extra = 0


@admin.register(HomeHeroBanner)
class HomeHeroBannerAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "page", "tag", "displayOrder", "isActive", "startsAt", "endsAt")
    list_editable = ("page", "displayOrder", "isActive")
    list_filter = ("page", "isActive")
    search_fields = ("title", "tag")
    filter_horizontal = ("businesses",)  # pick the (up to 2 rendered) featured businesses
    inlines = [BannerButtonInline, BannerMetricInline]


# ===== AUTO-REGISTER everything else in this app (legacy behavior kept) =====

app_models = apps.get_app_config("interior_advertisement").get_models()

for model in app_models:
    try:
        admin.site.register(model)
    except AlreadyRegistered:
        pass
