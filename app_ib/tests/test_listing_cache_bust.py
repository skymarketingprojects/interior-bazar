"""ponytail self-check (F227): a listing write must invalidate BOTH cache layers.

Products/services/catalogues are cached twice under different key schemes — the
controller (`product_detail_*`, `products_business_*`) and the view
(`cache:product:*`). _bustBusinessCache only cleared the list keys, so an edit
stayed invisible on the DETAIL endpoint for the full TTL and the seller
dashboard looked like the save had failed (this masked the F227 category fix).
Run from backend root: python app_ib/tests/test_listing_cache_bust.py
"""
import os
import sys

if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    os.environ["DJANGO_SETTINGS_MODULE"] = "interior_bazzar.settings"
    import django
    django.setup()

from django.core.cache import cache

from interior_products.Controllers.catelog.catelogController import CATELOG_CONTROLLER
from interior_products.Controllers.products.productsController import PRODUCTS_CONTROLLER
from interior_products.Controllers.services.servicesController import SERVICES_CONTROLLER

BIZ_ID, ITEM_ID = 4, 56

# (controller, both cache layers' detail keys, both layers' list keys)
CASES = (
    (PRODUCTS_CONTROLLER, ("product_detail_", "cache:product:"),
     ("products_business_", "cache:product:business:owner:")),
    (SERVICES_CONTROLLER, ("service_detail_", "cache:service:"),
     ("services_business_", "cache:service:business:owner:")),
    (CATELOG_CONTROLLER, ("catalogue_detail_", "cache:catalogue:"),
     ("catalogues_business_", "cache:catalogue:business:owner:")),
)


def _seed(detail_prefixes, list_prefixes):
    for p in detail_prefixes:
        cache.set(f"{p}{ITEM_ID}", "stale", 300)
    for p in list_prefixes:
        cache.set(f"{p}{BIZ_ID}", "stale", 300)


def test_write_busts_detail_and_list_on_both_layers():
    for ctrl, detail_prefixes, list_prefixes in CASES:
        _seed(detail_prefixes, list_prefixes)
        ctrl._bustBusinessCache(BIZ_ID, ITEM_ID)
        for p in detail_prefixes:
            assert cache.get(f"{p}{ITEM_ID}") is None, f"{ctrl.__name__}: {p} detail key survived"
        for p in list_prefixes:
            assert cache.get(f"{p}{BIZ_ID}") is None, f"{ctrl.__name__}: {p} list key survived"


def test_create_path_busts_lists_without_an_item_id():
    """Create has no id yet — it must still clear the lists, and must not crash."""
    for ctrl, detail_prefixes, list_prefixes in CASES:
        _seed(detail_prefixes, list_prefixes)
        ctrl._bustBusinessCache(BIZ_ID)
        for p in list_prefixes:
            assert cache.get(f"{p}{BIZ_ID}") is None, f"{ctrl.__name__}: {p} list key survived"


if __name__ == "__main__":
    test_write_busts_detail_and_list_on_both_layers()
    test_create_path_busts_lists_without_an_item_id()
    print("F227 OK: writes bust detail + list keys on both cache layers")
