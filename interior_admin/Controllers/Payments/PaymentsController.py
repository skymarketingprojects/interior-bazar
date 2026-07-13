from asgiref.sync import sync_to_async
from django.utils import timezone
from typing import Any, Dict, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES

from django.db.models import Q
from app_ib.models import TransectionData
from app_ib.Utils.Names import NAMES
from app_ib.Controllers.Plans.PlanController import PLAN_CONTROLLER
from interior_admin.Controllers.Audit.AuditController import append_audit
from .Validators.PaymentsValidators import RefundSchema, RejectPaymentSchema, PaymentListFilters


def _txn_dict(t: TransectionData) -> Dict[str, Any]:
    return {
        "id": t.id, "orderId": t.orderId, "transactionId": t.transactionId,
        "amount": t.amount, "paymentFor": t.paymentFor, "orderStatus": t.orderStatus,
        "paymentMethod": t.paymentMethod, "proofUrl": t.proofUrl,
        "refundStatus": t.refundStatus, "refundAmount": t.refundAmount,
        "refundReason": t.refundReason,
        "refundedBy": t.refundedBy.username if t.refundedBy_id else None,
        "refundedAt": t.refundedAt.isoformat() if t.refundedAt else None,
        "verifiedAt": t.verifiedAt.isoformat() if t.verifiedAt else None,
        "createdAt": t.createdAt.isoformat() if t.createdAt else "",
    }


class PaymentsController:

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def List(cls, queryParams: PaymentListFilters) -> Tuple[bool, Dict[str, Any]]:
        filters = Q()
        if queryParams.status:
            filters &= Q(orderStatus=queryParams.status)
        if queryParams.refunded is True:
            # Full refund history includes rejected refund requests, not just issued ones.
            filters &= Q(refundStatus__in=["REFUNDED", "REJECTED"])
        if queryParams.paymentMethod:
            filters &= Q(paymentMethod=queryParams.paymentMethod)
        pageNo = max(1, queryParams.pageNo or 1)
        pageSize = min(100, max(1, queryParams.pageSize or 20))
        start = (pageNo - 1) * pageSize
        qs = TransectionData.objects.filter(filters).select_related("refundedBy").order_by("-id")
        total = await qs.acount()
        rows = await sync_to_async(list)(qs[start:start + pageSize])
        return True, {"payments": [_txn_dict(t) for t in rows], "total": total, "pageNo": pageNo, "pageSize": pageSize}

    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.default_error,
        responseFunc=LocalResponse,
    )
    async def Refund(cls, txnId: int, payload: RefundSchema, actor=None) -> Tuple[bool, Dict[str, Any]]:
        """Level-3 action: record a refund (or refund rejection) against an
        existing TransectionData row, flip its orderStatus, and append an audit
        entry. Reuses TransectionData — does not create a parallel schema."""
        txn = await TransectionData.objects.filter(id=txnId).afirst()
        if txn is None:
            return False, {"message": "Transaction not found"}

        if txn.refundStatus == 'REFUNDED':
            return False, {"message": "Transaction is already refunded"}

        # Only money actually collected can be refunded. Gateway rows sit at "ACTIVE"
        # until the buyer returns and the order flips to PAID; refunding one that never
        # reached PAID would fabricate a refund against uncollected money.
        if txn.orderStatus != NAMES.CF_PAID:
            return False, {"message": "Only a paid transaction can be refunded"}

        if payload.reject:
            txn.refundStatus = 'REJECTED'
            txn.refundReason = payload.reason
            txn.refundedBy = actor if getattr(actor, "is_authenticated", False) else None
            txn.refundedAt = timezone.now()
            await sync_to_async(txn.save)()
            await append_audit(actor=actor, action='refund_rejected', module_key='refunds',
                               detail=f"txn={txn.transactionId} order={txn.orderId} reason={payload.reason}")
            return True, {"id": txn.id, "refundStatus": txn.refundStatus, "orderStatus": txn.orderStatus}

        amount = payload.amount if payload.amount not in (None, "") else txn.amount
        txn.refundStatus = 'REFUNDED'
        txn.refundAmount = amount
        txn.refundReason = payload.reason
        txn.refundedBy = actor if getattr(actor, "is_authenticated", False) else None
        txn.refundedAt = timezone.now()
        txn.orderStatus = 'REFUNDED'
        await sync_to_async(txn.save)()

        await append_audit(actor=actor, action='refund_approved', module_key='refunds',
                           detail=f"txn={txn.transactionId} order={txn.orderId} amount={amount} reason={payload.reason}")

        return True, {
            "id": txn.id,
            "orderStatus": txn.orderStatus,
            "refundStatus": txn.refundStatus,
            "refundAmount": txn.refundAmount,
            "refundedAt": txn.refundedAt.isoformat() if txn.refundedAt else None,
        }
    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Verify(cls, txnId: int, actor=None) -> Tuple[bool, Dict[str, Any]]:
        """Approve a SUBMITTED manual payment: mark PAID, stamp verifier, then
        reuse the standard activator (subscription active + buyer→seller)."""
        txn = await TransectionData.objects.filter(id=txnId).afirst()
        if txn is None:
            return False, {"message": "Transaction not found"}
        if txn.paymentMethod != 'manual' or txn.orderStatus != 'SUBMITTED':
            return False, {"message": "Only submitted manual payments can be verified"}

        txn.orderStatus = NAMES.CF_PAID  # 'PAID'
        txn.verifiedBy = actor if getattr(actor, "is_authenticated", False) else None
        txn.verifiedAt = timezone.now()
        await sync_to_async(txn.save)()

        # Activate the matching entity plan (BusinessPlan/Shop/Architect/Automation).
        await PLAN_CONTROLLER.ActivateEntityPlan(txn.transactionId)

        await append_audit(actor=actor, action='payment_verified', module_key='payments',
                           detail=f"txn={txn.transactionId} order={txn.orderId} amount={txn.amount}")
        return True, _txn_dict(txn)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Reject(cls, txnId: int, payload: RejectPaymentSchema, actor=None) -> Tuple[bool, Dict[str, Any]]:
        """Reject a SUBMITTED manual payment — mark REJECTED, no activation."""
        txn = await TransectionData.objects.filter(id=txnId).afirst()
        if txn is None:
            return False, {"message": "Transaction not found"}
        if txn.paymentMethod != 'manual' or txn.orderStatus != 'SUBMITTED':
            return False, {"message": "Only submitted manual payments can be rejected"}

        txn.orderStatus = 'REJECTED'
        txn.verifiedBy = actor if getattr(actor, "is_authenticated", False) else None
        txn.verifiedAt = timezone.now()
        await sync_to_async(txn.save)()

        await append_audit(actor=actor, action='payment_rejected', module_key='payments',
                           detail=f"txn={txn.transactionId} order={txn.orderId} reason={payload.reason}")
        return True, _txn_dict(txn)


PAYMENTS_CONTROLLER = PaymentsController()
