from asgiref.sync import sync_to_async
from django.utils import timezone
from typing import Any, Dict, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES

from app_ib.models import TransectionData
from interior_admin.Controllers.Audit.AuditController import append_audit
from .Validators.PaymentsValidators import RefundSchema


class PaymentsController:

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


PAYMENTS_CONTROLLER = PaymentsController()
