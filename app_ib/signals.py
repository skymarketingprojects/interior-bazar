from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import (
    Pages, QNA, StockMedia, OfferText, Blog, 
    BusinessType, BusinessCategory, BusinessSegment, 
    Country, State
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

# --- Common / Structural Data ---

@receiver([post_save, post_delete], sender=Pages)
def clear_pages_cache(sender, **kwargs):
    clear_cache_pattern("cache:page:*")

@receiver([post_save, post_delete], sender=QNA)
def clear_qna_cache(sender, **kwargs):
    cache.delete("cache:qna:all")

@receiver([post_save, post_delete], sender=StockMedia)
def clear_stockmedia_cache(sender, **kwargs):
    clear_cache_pattern("cache:stockmedia:*")

@receiver([post_save, post_delete], sender=OfferText)
def clear_offertext_cache(sender, **kwargs):
    cache.delete("cache:offertext")

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
    cache.delete(f"cache:catalogue:{instance.id}")
    # Clear business lists
    if instance.business:
        cache.delete(f"cache:catalogue:business:{instance.business.id}")
        cache.delete(f"cache:catalogue:business:owner:{instance.business.id}")
    # Clear related and all
    clear_cache_pattern("cache:catalogue:all:*")
    clear_cache_pattern("cache:catalogue:related:*")
    # Also clear tabs as they might be affected
    clear_cache_pattern("cache:product:tabs:*")

@receiver([post_save, post_delete], sender=Product)
def clear_product_cache(sender, instance, **kwargs):
    cache.delete(f"cache:product:{instance.id}")
    if instance.business:
        cache.delete(f"cache:product:business:{instance.business.id}")
        cache.delete(f"cache:product:business:owner:{instance.business.id}")
    clear_cache_pattern("cache:product:all:*")
    clear_cache_pattern("cache:product:related:*")
    clear_cache_pattern("cache:product:tabs:*")

@receiver([post_save, post_delete], sender=Service)
def clear_service_cache(sender, instance, **kwargs):
    cache.delete(f"cache:service:{instance.id}")
    if instance.business:
        cache.delete(f"cache:service:business:{instance.business.id}")
        cache.delete(f"cache:service:business:owner:{instance.business.id}")
    clear_cache_pattern("cache:service:all:*")
    clear_cache_pattern("cache:service:related:*")
    clear_cache_pattern("cache:product:tabs:*")

@receiver([post_save, post_delete], sender=ProductCategory)
@receiver([post_save, post_delete], sender=ProductSubCategory)
def clear_product_categories_cache(sender, **kwargs):
    cache.delete("cache:product:categories")
    cache.delete("cache:product:sub_categories")
    clear_cache_pattern("cache:product:tabs:*")

@receiver([post_save, post_delete], sender=InteriorServices)
def clear_own_services_cache(sender, **kwargs):
    clear_cache_pattern("cache:service:own:*")

# --- Leads / GMB ---

@receiver([post_save, post_delete], sender=GMBBusiness)
def clear_gmb_kpis_cache(sender, **kwargs):
    cache.delete("cache:leads:kpis")
