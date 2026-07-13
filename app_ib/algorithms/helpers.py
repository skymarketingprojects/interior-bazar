"""Shared infrastructure for the engine algorithms: entity registry,
ContentType resolution, owner lookup, and a small math helper.
"""
import math
from django.apps import apps
from django.contrib.contenttypes.models import ContentType

from app_ib.Utils.EngineConfig import ENTITY_TYPE


# entity_type string -> (app_label, model_name)
ENTITY_MODELS = {
    ENTITY_TYPE.BUSINESS: ("interior_business", "Business"),
    ENTITY_TYPE.SHOP: ("interior_engine", "Shop"),
    ENTITY_TYPE.ARCHITECT: ("interior_engine", "Architect"),
    ENTITY_TYPE.PRODUCT: ("interior_products", "Product"),
    ENTITY_TYPE.SERVICE: ("interior_products", "Service"),
    ENTITY_TYPE.CATELOGUE: ("interior_products", "Catelogue"),
}


def get_model(entity_type):
    app_label, model_name = ENTITY_MODELS[entity_type]
    return apps.get_model(app_label, model_name)


def content_type_for(entity_type):
    return ContentType.objects.get_for_model(get_model(entity_type))


def entity_type_of(instance):
    """Reverse map a model instance -> entity_type string (or None)."""
    name = instance.__class__.__name__
    for et, (_, model_name) in ENTITY_MODELS.items():
        if model_name == name:
            return et
    return None


def owner_user_id(instance):
    """User id that owns an entity (for self-view exclusion). Products/Services/
    Catelogues are owned via their business.user."""
    et = entity_type_of(instance)
    if et in (ENTITY_TYPE.BUSINESS, ENTITY_TYPE.SHOP, ENTITY_TYPE.ARCHITECT):
        return getattr(instance, "user_id", None)
    biz = getattr(instance, "business", None)
    return getattr(biz, "user_id", None) if biz else None


def entity_city(instance):
    """Best-effort city string for an entity (for city-dimension trending)."""
    et = entity_type_of(instance)
    if et == ENTITY_TYPE.ARCHITECT:
        return getattr(instance, "city", "") or ""
    if et == ENTITY_TYPE.SHOP:
        loc = instance.location_set.first() if hasattr(instance, "location_set") else None
        return getattr(loc, "city", "") if loc else ""
    if et == ENTITY_TYPE.BUSINESS:
        loc = getattr(instance, "business_location", None)
        return getattr(loc, "city", "") if loc else ""
    return ""


def haversine_km(lat1, lng1, lat2, lng2):
    """Great-circle distance in km. Earth radius 6371 km."""
    from app_ib.Utils.EngineConfig import ALGO
    r = ALGO.EARTH_RADIUS_KM
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))
