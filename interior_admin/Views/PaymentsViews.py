from adrf.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.decorators.ViewDecorator import exceptionHandler

from interior_admin.Controllers.Payments.PaymentsController import PAYMENTS_CONTROLLER
from interior_admin.Controllers.Payments.Validators.PaymentsValidators import RefundSchema, RejectPaymentSchema, PaymentListFilters
from interior_admin.Validators.adminValidators import hasAccess


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def PaymentsListView(request: Request):
    """GET /api/v1/admin/payments/ — transactions, filter by status/refunded."""
    await hasAccess(request=request)
    return await PAYMENTS_CONTROLLER.List(queryParams=PaymentListFilters(**request.query_params.dict()))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@exceptionHandler(
    errorMessage=RESPONSE_MESSAGES.default_error,
    responseFunc=ServerResponse
)
async def RefundView(request: Request, txnId: int):
    """POST /api/v1/admin/payments/<txnId>/refund/ — level-3. Body: {amount?,
    reason, reject?}. Records a refund (or rejection) on the TransectionData row
    and appends an audit entry. Admin-gated."""
    await hasAccess(request=request)
    payload = RefundSchema(**request.data)
    return await PAYMENTS_CONTROLLER.Refund(txnId=txnId, payload=payload, actor=request.user)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def VerifyView(request: Request, txnId: int):
    """POST /api/v1/admin/payments/<txnId>/verify/ — approve a SUBMITTED manual
    payment: mark PAID, stamp verifier, activate the entity plan. Admin-gated."""
    await hasAccess(request=request)
    return await PAYMENTS_CONTROLLER.Verify(txnId=txnId, actor=request.user)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def RejectView(request: Request, txnId: int):
    """POST /api/v1/admin/payments/<txnId>/reject/ — reject a SUBMITTED manual
    payment. Body: {reason?}. No activation. Admin-gated."""
    await hasAccess(request=request)
    return await PAYMENTS_CONTROLLER.Reject(txnId=txnId, payload=RejectPaymentSchema(**request.data), actor=request.user)
