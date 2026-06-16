"""Shop / Architect / Review CRUD views (sync DRF). Writes require auth."""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Controllers.Engine.CrudController import (
    CRUD_CONTROLLER, NotFound_, PermissionError_, Conflict_,
)


def _ok(data, msg="ok"):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=msg, data=data)


def _err(e):
    if isinstance(e, NotFound_):
        return ServerResponse(response=False, code=RESPONSE_CODES.not_exist, message=str(e), data={})
    if isinstance(e, PermissionError_):
        return ServerResponse(response=False, code=RESPONSE_CODES.forbidden, message=str(e), data={})
    if isinstance(e, Conflict_):
        return ServerResponse(response=False, code=RESPONSE_CODES.conflict, message=str(e), data={})
    return ServerResponse(response=False, code=RESPONSE_CODES.error, message=str(e), data={})


# ---------------- Shop ----------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ShopCreateView(request):
    try:
        return _ok(CRUD_CONTROLLER.create_shop(request.user, request.data), "Shop created")
    except Exception as e:
        return _err(e)


@api_view(["PUT", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def ShopUpdateDeleteView(request, shopId):
    try:
        if request.method == "DELETE":
            CRUD_CONTROLLER.delete_shop(request.user, shopId)
            return _ok({}, "Shop deleted")
        return _ok(CRUD_CONTROLLER.update_shop(request.user, shopId, request.data), "Shop updated")
    except Exception as e:
        return _err(e)


# ---------------- Business (engine create, buy-first) ----------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def BusinessCreateView(request):
    try:
        return _ok(CRUD_CONTROLLER.create_business(request.user, request.data), "Business created")
    except Exception as e:
        return _err(e)


# ---------------- Architect ----------------
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ArchitectCreateView(request):
    try:
        return _ok(CRUD_CONTROLLER.create_architect(request.user, request.data), "Architect created")
    except Exception as e:
        return _err(e)


@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated])
def ArchitectUpdateView(request, architectId):
    try:
        return _ok(CRUD_CONTROLLER.update_architect(request.user, architectId, request.data),
                   "Architect updated")
    except Exception as e:
        return _err(e)


# ---------------- Review ----------------
@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def ReviewListCreateView(request):
    if request.method == "POST":
        if not request.user or not request.user.is_authenticated:
            return ServerResponse(response=False, code=RESPONSE_CODES.auth_error,
                                  message="authentication required", data={})
        try:
            return _ok(CRUD_CONTROLLER.create_review(request.user, request.data), "Review submitted")
        except Exception as e:
            return _err(e)
    et = request.GET.get("entityType")
    oid = request.GET.get("objectId")
    if not et or not oid:
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request,
                              message="entityType and objectId required", data={})
    try:
        return _ok(CRUD_CONTROLLER.list_reviews(et, int(oid)))
    except Exception as e:
        return _err(e)


@api_view(["PUT", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def ReviewUpdateDeleteView(request, reviewId):
    try:
        if request.method == "DELETE":
            CRUD_CONTROLLER.delete_review(request.user, reviewId)
            return _ok({}, "Review deleted")
        return _ok(CRUD_CONTROLLER.update_review(request.user, reviewId, request.data), "Review updated")
    except Exception as e:
        return _err(e)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ReviewHelpfulView(request, reviewId):
    try:
        return _ok(CRUD_CONTROLLER.mark_helpful(reviewId), "Marked helpful")
    except Exception as e:
        return _err(e)
