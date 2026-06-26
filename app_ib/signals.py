from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import (
    Pages, QNA, StockMedia, OfferText, Blog,
    BusinessType, BusinessCategory, BusinessSegment,
    Country, State,
    Business, BusinessProfile,
)
from interior_products.models import (
    Catelogue, Product, Service,
    ProductCategory, ProductSubCategory, InteriorServices
)
from interior_admin.models import GMBBusiness

def clear_cache_pattern(pattern):
    """Utility to clear cache by pattern using django-redis."""
    try:
        # django-redis specific method
        cache.delete_pattern(pattern)
    except Exception:
        # If pattern delete fails, we might need a fallback or just log it
        pass

def cache_delete(*keys):
    """Best-effort cache delete: a Redis outage must NOT fail the write that
    triggered this post_save/post_delete signal (see ISSUE-001 / F3). Each bad
    key is swallowed independently so one failure can't skip the rest."""
    for key in keys:
        try:
            cache.delete(key)
        except Exception:
            pass

# --- Common / Structural Data ---

@receiver([post_save, post_delete], sender=Pages)
def clear_pages_cache(sender, **kwargs):
    clear_cache_pattern("cache:page:*")

@receiver([post_save, post_delete], sender=QNA)
def clear_qna_cache(sender, **kwargs):
    cache_delete("cache:qna:all")

@receiver([post_save, post_delete], sender=StockMedia)
def clear_stockmedia_cache(sender, **kwargs):
    clear_cache_pattern("cache:stockmedia:*")

@receiver([post_save, post_delete], sender=OfferText)
def clear_offertext_cache(sender, **kwargs):
    cache_delete("cache:offertext")

@receiver([post_save, post_delete], sender=Blog)
def clear_blog_cache(sender, instance, **kwargs):
    clear_cache_pattern("cache:blog:*")

# --- Business Structural Data ---

@receiver([post_save, post_delete], sender=BusinessType)
@receiver([post_save, post_delete], sender=BusinessCategory)
@receiver([post_save, post_delete], sender=BusinessSegment)
def clear_business_structural_cache(sender, **kwargs):
    clear_cache_pattern("cache:business:*")

@receiver([post_save, post_delete], sender=Country)
@receiver([post_save, post_delete], sender=State)
def clear_location_cache(sender, **kwargs):
    clear_cache_pattern("cache:location:*")

# --- Products / Services / Catalogues ---

@receiver([post_save, post_delete], sender=Catelogue)
def clear_catalogue_cache(sender, instance, **kwargs):
    # Clear specific item
    cache_delete(f"cache:catalogue:{instance.id}")
    # Clear business lists
    if instance.business:
        cache_delete(
            f"cache:catalogue:business:{instance.business.id}",
            f"cache:catalogue:business:owner:{instance.business.id}",
            # The owner-list controller (catelogController.GetCatelogForBusiness)
            # caches under THIS key — must be cleared or created items stay hidden.
            f"catalogues_business_{instance.business.id}",
        )
    # Clear related and all
    clear_cache_pattern("cache:catalogue:all:*")
    clear_cache_pattern("cache:catalogue:related:*")
    # Also clear tabs as they might be affected
    clear_cache_pattern("cache:product:tabs:*")

@receiver([post_save, post_delete], sender=Product)
def clear_product_cache(sender, instance, **kwargs):
    cache_delete(f"cache:product:{instance.id}")
    if instance.business:
        cache_delete(
            f"cache:product:business:{instance.business.id}",
            f"cache:product:business:owner:{instance.business.id}",
            # productsController.getProductsForBusiness caches the owner list here.
            f"products_business_{instance.business.id}",
        )
    clear_cache_pattern("cache:product:all:*")
    clear_cache_pattern("cache:product:related:*")
    clear_cache_pattern("cache:product:tabs:*")

@receiver([post_save, post_delete], sender=Service)
def clear_service_cache(sender, instance, **kwargs):
    cache_delete(f"cache:service:{instance.id}")
    if instance.business:
        cache_delete(
            f"cache:service:business:{instance.business.id}",
            f"cache:service:business:owner:{instance.business.id}",
            # servicesController.getServicesForBusiness caches the owner list here.
            f"services_business_{instance.business.id}",
        )
    clear_cache_pattern("cache:service:all:*")
    clear_cache_pattern("cache:service:related:*")
    clear_cache_pattern("cache:product:tabs:*")

@receiver([post_save, post_delete], sender=ProductCategory)
@receiver([post_save, post_delete], sender=ProductSubCategory)
def clear_product_categories_cache(sender, **kwargs):
    cache_delete("cache:product:categories", "cache:product:sub_categories")
    clear_cache_pattern("cache:product:tabs:*")

@receiver([post_save, post_delete], sender=InteriorServices)
def clear_own_services_cache(sender, **kwargs):
    clear_cache_pattern("cache:service:own:*")

# --- Leads / GMB ---

@receiver([post_save, post_delete], sender=GMBBusiness)
def clear_gmb_kpis_cache(sender, **kwargs):
    cache_delete("cache:leads:kpis")


# --- AI Specialization bootstrap (one-time, debounced) ---
# Arm/re-arm the bootstrap job while the owner is still populating the business.
# enqueue_bootstrap_refresh() is a no-op once a BusinessSpecialization exists, so
# these become inert after the first generation (ongoing regen = drift cron).

# Engine writes that must NOT re-arm the bootstrap (completion algo / slug autogen).
_SPEC_IGNORED_FIELDS = {"completionPercent", "canGoLive", "slug"}


def _enqueue_spec(business, reason):
    if business is None:
        return
    from app_ib.algorithms.specialization import enqueue_bootstrap_refresh
    enqueue_bootstrap_refresh(business, reason=reason)


def _is_engine_only_save(kwargs):
    update_fields = kwargs.get("update_fields")
    return bool(update_fields) and set(update_fields).issubset(_SPEC_IGNORED_FIELDS)


@receiver(post_save, sender=Business)
def spec_on_business_save(sender, instance, **kwargs):
    if _is_engine_only_save(kwargs):
        return
    _enqueue_spec(instance, "business")


@receiver(post_save, sender=BusinessProfile)
def spec_on_business_profile_save(sender, instance, **kwargs):
    _enqueue_spec(getattr(instance, "business", None), "profile")


@receiver([post_save, post_delete], sender=Product)
def spec_on_product_change(sender, instance, **kwargs):
    _enqueue_spec(getattr(instance, "business", None), "product")


@receiver([post_save, post_delete], sender=Service)
def spec_on_service_change(sender, instance, **kwargs):
    _enqueue_spec(getattr(instance, "business", None), "service")


# --- Inbound engagement feed: "someone filled your form" ---
from .models import LeadQuery


@receiver(post_save, sender=LeadQuery)
def engagement_on_lead_created(sender, instance, created, **kwargs):
    """Record an inbound 'enquiry' engagement when a new lead/form lands on a
    seller's entity (product/service → that item, else the business). Fire-and-
    forget: never let feed-writing break lead creation."""
    if not created:
        return
    try:
        from app_ib.algorithms.state import record_engagement
        from app_ib.Utils.EngineConfig import ENGAGEMENT_VERB, ENTITY_TYPE

        if instance.product_id:
            entity_type, object_id = ENTITY_TYPE.PRODUCT, instance.product_id
        elif instance.service_id:
            entity_type, object_id = ENTITY_TYPE.SERVICE, instance.service_id
        elif instance.business_id:
            entity_type, object_id = ENTITY_TYPE.BUSINESS, instance.business_id
        else:
            return
        record_engagement(ENGAGEMENT_VERB.ENQUIRY, entity_type, object_id,
                           actor=instance.user, actor_name=(instance.name or "").strip())
    except Exception:
        pass
