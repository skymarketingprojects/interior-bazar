"""
v3-only market views — Redis-free product detail flow for /v3/products/:slug.

NEW endpoints (additive; the legacy endpoints in views.py are frozen for the
old frontend and stay untouched):

    GET v1/market/v3/product/<slugOrId>/                → full detail payload
    GET v1/market/v3/product/<productId>/related/       → category-related rail
    GET v1/market/v3/product/<productId>/from-business/ → same-seller rail

Canonical responder stack (task 21): sync DRF @api_view functions wrapped by
@exceptionHandler(responseFunc=ServerResponse, errorMessage=...) — the decorator maps any
exception to a clean envelope (no per-view try/except, no local _serve/_error wrappers);
views pass the controller's LocalResponse straight through as a ServerResponse. No cache
reads/writes — every request hits the ORM directly, so the page keeps working with Redis down.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.decorators.ViewDecorator import exceptionHandler
from .Controllers.products.productsV3Controller import PRODUCTS_V3_CONTROLLER


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.product_fetch_error)
def ProductDetailV3View(request, slugOrId: str):
    local = PRODUCTS_V3_CONTROLLER.getProductDetailV3(slugOrId)
    return ServerResponse(response=local.response, code=local.code, message=local.message, data=local.data)


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.product_fetch_error)
def RelatedProductsV3View(request, productId: int):
    limit = request.GET.get('limit', None)
    local = PRODUCTS_V3_CONTROLLER.getRelatedProductsV3(productId, int(limit) if limit else 10)
    return ServerResponse(response=local.response, code=local.code, message=local.message, data=local.data)


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.product_fetch_error)
def BusinessProductsV3View(request, productId: int):
    limit = request.GET.get('limit', None)
    local = PRODUCTS_V3_CONTROLLER.getBusinessProductsV3(productId, int(limit) if limit else 10)
    return ServerResponse(response=local.response, code=local.code, message=local.message, data=local.data)
