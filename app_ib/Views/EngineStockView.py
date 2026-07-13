"""
EngineStockView — HTTP layer for product stock / service availability.

Canonical responder stack (task 20): @exceptionHandler(responseFunc=ServerResponse,
errorMessage=...) wraps each view — the decorator maps controller NotFound_/
PermissionError_ to 410/403 and any other exception to a clean envelope; views return
ServerResponse(...) directly (no local _ok/_err/_bad wrappers). camelCase JSON; body
`code` carries the semantic status because ServerResponse always answers HTTP 200.

The `int(...)`-parse guards keep their explicit `except (TypeError, ValueError)` so the
user-facing "quantity must be an integer" message survives (the decorator would degrade
a bare ValueError to a generic "Bad request").

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
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.decorators.ViewDecorator import exceptionHandler
import app_ib.Controllers.Engine.StockController as SC


# ==========================================================================
# Product availability (public)
# ==========================================================================
@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ProductAvailabilityView(request, productId):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=SC.product_availability(productId))


# ==========================================================================
# Service availability — GET public (+isOwner when authed), PATCH owner-only
# ==========================================================================
@api_view(["GET", "PATCH"])
@permission_classes([AllowAny])  # PATCH enforces auth manually below — one URL, two access levels
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ServiceAvailabilityView(request, serviceId):
    if request.method == "GET":
        return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                              data=SC.service_availability(serviceId, user=request.user))
    # PATCH
    user = getattr(request, "user", None)
    if not (user and user.is_authenticated):
        return ServerResponse(response=False, code=RESPONSE_CODES.auth_error,
                              message=RESPONSE_MESSAGES.authentication_required, data={})
    is_available = (request.data or {}).get("isAvailable", None)
    if not isinstance(is_available, bool):
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request,
                              message=RESPONSE_MESSAGES.is_available_required, data={})
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=SC.service_availability_set(user, serviceId, is_available))


# ==========================================================================
# Product stock check (public — buyers run this pre-enquiry; the atomic
# reserve variant is controller-only until an engine order flow exists)
# ==========================================================================
@api_view(["POST"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ProductStockCheckView(request, productId):
    try:
        quantity = int((request.data or {}).get("quantity", 0))
    except (TypeError, ValueError):
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request,
                              message=RESPONSE_MESSAGES.quantity_must_be_integer, data={})
    if quantity < 1:
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request,
                              message=RESPONSE_MESSAGES.quantity_must_be_positive, data={})
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=SC.product_stock_check(productId, quantity))
