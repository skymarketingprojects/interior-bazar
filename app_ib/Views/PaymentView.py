from adrf.decorators import api_view
from app_ib.Controllers.PaymentGateway.PaymentGatewayController import PaymentGatewayController
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated

@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def InitiatePaymentView(request):
    try:
        data = request.data
        user = request.user

        payment_resp = await PaymentGatewayController.InitiatePayment(data=data,userId=user.id)

        return ServerResponse(
            response=payment_resp.response,
            message=payment_resp.message,
            code=payment_resp.code,
            data=payment_resp.data
        )

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message="Payment initiation error",
            code=RESPONSE_CODES.error,
            data={"error": str(e)}
        )


@api_view(['POST'])
async def CheckPaymentStatusView(request):
    try:
        transactionId = request.data.get("transactionId")
        status_resp = await PaymentGatewayController.CheckPaymentStatus(transactionId)
        

        return ServerResponse(
            response=status_resp.response,
            message=status_resp.message,
            code=status_resp.code,
            data=status_resp.data
        )

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message="Error checking status",
            code=RESPONSE_CODES.error,
            data={"error": str(e)}
        )
@api_view(['POST'])
async def RefundTransactionView(request):
    try:
        data = request.data
        transaction_id = data.get("transaction_id")
        amount = data.get("amount")

        refund_resp = await PaymentGatewayController.RefundTransaction(transaction_id, amount)

        return ServerResponse(
            response=refund_resp.response,
            message=refund_resp.message,
            code=refund_resp.code,
            data=refund_resp.data
        )

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message="Error processing refund",
            code=RESPONSE_CODES.error,
            data={"error": str(e)}
        )   