"""ponytail self-check (F226): saved/recently-viewed cards must carry an imageUrl.

EngineController._image() only read cover fields (coverImageUrl/coverImage/
catelougeImage), so Products/Services — which keep images on related rows —
always returned "" and every card for them rendered imageless. All seven
_image() callers shared the bug, so the fix is in the helper.
Run from backend root: python app_ib/tests/test_saved_card_images.py
"""
import os
import sys

if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    os.environ["DJANGO_SETTINGS_MODULE"] = "interior_bazzar.settings"
    import django
    django.setup()

from app_ib.Controllers.Engine.EngineController import _image
from interior_products.models import Product, Service


def _with_related_image(model, rel):
    """First row that genuinely has a related image — the case _image() used to miss."""
    for obj in model.objects.all()[:200]:
        mgr = getattr(obj, rel, None)
        if mgr is not None and mgr.exists():
            return obj
    return None


def test_product_and_service_resolve_related_images():
    for model, rel in ((Product, "productImages"), (Service, "serviceImages")):
        obj = _with_related_image(model, rel)
        if obj is None:
            print(f"  skip {model.__name__}: no row with a related image in this DB")
            continue
        got = _image(obj)
        assert got, f"{model.__name__} {obj.id} has a {rel} row but _image() returned ''"
        assert got == obj.__getattribute__(rel).all()[0].image, "must return the first related image"


def test_cover_field_still_wins():
    """A cover URL must take precedence over the related-row fallback."""
    class FakeCover:
        coverImageUrl = "https://cdn.example/cover.jpg"
        productImages = None

    assert _image(FakeCover()) == "https://cdn.example/cover.jpg"


def test_imageless_object_returns_empty_string_not_none():
    """Cards fall back to their icon on "" — None would render as the string 'None'."""
    class Bare:
        pass

    assert _image(Bare()) == ""


if __name__ == "__main__":
    test_product_and_service_resolve_related_images()
    test_cover_field_still_wins()
    test_imageless_object_returns_empty_string_not_none()
    print("F226 OK: related-row images resolve; cover still wins; imageless -> ''")
