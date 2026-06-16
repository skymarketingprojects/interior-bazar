"""
v3-only market views — Redis-free product detail flow for /v3/products/:slug.

NEW endpoints (additive; the legacy endpoints in views.py are frozen for the
old frontend and stay untouched):

    GET v1/market/v3/product/<slugOrId>/                → full detail payload
    GET v1/market/v3/product/<productId>/related/       → category-related rail
    GET v1/market/v3/product/<productId>/from-business/ → same-seller rail

Plain sync DRF views (same style as the engine layer). No cache reads/writes —
every request hits the ORM directly, so the page keeps working with Redis down.
"""
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from .Controllers.products.productsV3Controller import PRODUCTS_V3_CONTROLLER


def _serve(local) -> ServerResponse:
    return ServerResponse(
        response=local.response,
        message=local.message,
        code=local.code,
        data=local.data,
    )


def _error(exc: Exception) -> ServerResponse:
    return ServerResponse(
        response=RESPONSE_MESSAGES.error,
        message=RESPONSE_MESSAGES.product_fetch_error,
        code=RESPONSE_CODES.error,
        data={'error': str(exc)},
    )


class ProductDetailV3View(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slugOrId: str) -> ServerResponse:
        try:
            return _serve(PRODUCTS_V3_CONTROLLER.getProductDetailV3(slugOrId))
        except Exception as e:
            return _error(e)


class RelatedProductsV3View(APIView):
    permission_classes = [AllowAny]

    def get(self, request, productId: int) -> ServerResponse:
        try:
            limit = request.GET.get('limit', None)
            return _serve(PRODUCTS_V3_CONTROLLER.getRelatedProductsV3(productId, int(limit) if limit else 10))
        except Exception as e:
            return _error(e)


class BusinessProductsV3View(APIView):
    permission_classes = [AllowAny]

    def get(self, request, productId: int) -> ServerResponse:
        try:
            limit = request.GET.get('limit', None)
            return _serve(PRODUCTS_V3_CONTROLLER.getBusinessProductsV3(productId, int(limit) if limit else 10))
        except Exception as e:
            return _error(e)
