"""
EngineStockView — HTTP layer for product stock / service availability.

Follows the EngineGapsView conventions (sync DRF @api_view, _ok/_err/_bad
wrappers, camelCase JSON, body `code` carries the semantic status because
ServerResponse always answers HTTP 200).

Auth model:
- GET availability endpoints are AllowAny (detail pages are public), but the
  service GET inspects request.user when a JWT is present so it can return
  isOwner for the owner's toggle.
- PATCH service availability requires auth + ownership (owner check lives in
  the controller and raises PermissionError_ -> code 403).
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Controllers.Engine.CrudController import NotFound_, PermissionError_
import app_ib.Controllers.Engine.StockController as SC


def _ok(data, msg="ok"):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=msg, data=data)


def _err(e):
    if isinstance(e, NotFound_):
        return ServerResponse(response=False, code=RESPONSE_CODES.not_exist, message=str(e), data={})
    if isinstance(e, PermissionError_):
        return ServerResponse(response=False, code=RESPONSE_CODES.forbidden, message=str(e), data={})
    return ServerResponse(response=False, code=RESPONSE_CODES.error, message=str(e), data={})


def _bad(msg="bad request"):
    return ServerResponse(response=False, code=RESPONSE_CODES.bad_request, message=msg, data={})


# ==========================================================================
# Product availability (public)
# ==========================================================================
@api_view(["GET"])
@permission_classes([AllowAny])
def ProductAvailabilityView(request, productId):
    try:
        return _ok(SC.product_availability(productId))
    except Exception as e:
        return _err(e)


# ==========================================================================
# Service availability — GET public (+isOwner when authed), PATCH owner-only
# ==========================================================================
@api_view(["GET", "PATCH"])
@permission_classes([AllowAny])  # PATCH enforces auth manually below — one URL, two access levels
def ServiceAvailabilityView(request, serviceId):
    try:
        if request.method == "GET":
            return _ok(SC.service_availability(serviceId, user=request.user))
        # PATCH
        user = getattr(request, "user", None)
        if not (user and user.is_authenticated):
            return ServerResponse(response=False, code=RESPONSE_CODES.auth_error,
                                  message="authentication required", data={})
        is_available = (request.data or {}).get("isAvailable", None)
        if not isinstance(is_available, bool):
            return _bad("isAvailable (boolean) required")
        return _ok(SC.service_availability_set(user, serviceId, is_available))
    except Exception as e:
        return _err(e)


# ==========================================================================
# Product stock check (public — buyers run this pre-enquiry; the atomic
# reserve variant is controller-only until an engine order flow exists)
# ==========================================================================
@api_view(["POST"])
@permission_classes([AllowAny])
def ProductStockCheckView(request, productId):
    try:
        quantity = int((request.data or {}).get("quantity", 0))
    except (TypeError, ValueError):
        return _bad("quantity must be an integer")
    if quantity < 1:
        return _bad("quantity must be >= 1")
    try:
        return _ok(SC.product_stock_check(productId, quantity))
    except Exception as e:
        return _err(e)
