"""Shop / Architect / Review CRUD views (sync DRF). Writes require auth.

Canonical responder stack (task 20): @exceptionHandler(responseFunc=ServerResponse,
errorMessage=...) wraps each view — the decorator maps controller NotFound_/
PermissionError_/Conflict_ to 410/403/409 and any other exception to a clean envelope;
views return ServerResponse(...) directly (no local _ok/_err wrappers, no per-view try/except)."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.decorators.ViewDecorator import exceptionHandler
from app_ib.Controllers.Engine.CrudController import CRUD_CONTROLLER


# ---------------- Shop ----------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ShopCreateView(request):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.shop_created,
                          data=CRUD_CONTROLLER.create_shop(request.user, request.data))


@api_view(["PUT", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ShopUpdateDeleteView(request, shopId):
    if request.method == "DELETE":
        CRUD_CONTROLLER.delete_shop(request.user, shopId)
        return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.shop_deleted, data={})
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.shop_updated,
                          data=CRUD_CONTROLLER.update_shop(request.user, shopId, request.data))


# ---------------- Business (engine create, buy-first) ----------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def BusinessCreateView(request):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.engine_business_created,
                          data=CRUD_CONTROLLER.create_business(request.user, request.data))


# ---------------- Architect ----------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ArchitectCreateView(request):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.architect_created,
                          data=CRUD_CONTROLLER.create_architect(request.user, request.data))


@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ArchitectUpdateView(request, architectId):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.architect_updated,
                          data=CRUD_CONTROLLER.update_architect(request.user, architectId, request.data))


# ---------------- Review ----------------
@api_view(["GET", "POST"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ReviewListCreateView(request):
    if request.method == "POST":
        if not request.user or not request.user.is_authenticated:
            return ServerResponse(response=False, code=RESPONSE_CODES.auth_error,
                                  message=RESPONSE_MESSAGES.authentication_required, data={})
        return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.review_submitted,
                              data=CRUD_CONTROLLER.create_review(request.user, request.data))
    et = request.GET.get("entityType")
    oid = request.GET.get("objectId")
    if not et or not oid:
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request,
                              message=RESPONSE_MESSAGES.entity_object_required, data={})
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok,
                          data=CRUD_CONTROLLER.list_reviews(et, int(oid)))


@api_view(["PUT", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ReviewUpdateDeleteView(request, reviewId):
    if request.method == "DELETE":
        CRUD_CONTROLLER.delete_review(request.user, reviewId)
        return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.review_deleted, data={})
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.review_updated,
                          data=CRUD_CONTROLLER.update_review(request.user, reviewId, request.data))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ReviewHelpfulView(request, reviewId):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.review_marked_helpful,
                          data=CRUD_CONTROLLER.mark_helpful(reviewId))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ReviewReplyView(request, reviewId):
    # Seller posts a reply (+ optional attribute tags) to a review of their entity.
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.review_reply_posted,
                          data=CRUD_CONTROLLER.reply_to_review(
                              request.user, reviewId,
                              (request.data or {}).get("text", ""),
                              (request.data or {}).get("tags")))
