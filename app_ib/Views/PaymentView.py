from adrf.decorators import api_view
from app_ib.Controllers.PaymentGateway.PaymentGatewayController import PaymentGatewayController
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated

paymentFor = {
    NAMES.PLAN: PaymentGatewayController.InitiatePlanPayment,
    NAMES.ADVERTISEMENT: PaymentGatewayController.InitiateADSPayment
}

@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def InitiatePaymentView(request):
    try:
        data = request.data
        user = request.user
        serviceType = data.get(NAMES.PAYMENT_FOR,NAMES.EMPTY)
        if serviceType not in paymentFor:
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                message='Invalid payment type',
                code=RESPONSE_CODES.error,
                data={}
            )

        payment_resp = await paymentFor[serviceType](data=data.get(NAMES.DATA), user=user, redirectUrl=data.get(NAMES.REDIRECT_URL,NAMES.EMPTY))

        return ServerResponse(
            response=payment_resp.response,
            message=payment_resp.message,
            code=payment_resp.code,
            data=payment_resp.data
        )

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message='Payment initiation error',
            code=RESPONSE_CODES.error,
            data={NAMES.ERROR: str(e)}
        )

@api_view(['POST'])
async def CheckPaymentStatusView(request):
    try:
        transactionId = request.data.get(NAMES.TRANSACTION)
        status_resp = await PaymentGatewayController.CheckPaymentStatus(transactionId,request.data)
        

        return ServerResponse(
            response=status_resp.response,
            message=status_resp.message,
            code=status_resp.code,
            data=status_resp.data
        )

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message='Error checking status',
            code=RESPONSE_CODES.error,
            data={NAMES.ERROR: str(e)}
        )
@api_view(['POST'])
async def RefundTransactionView(request):
    try:
        data = request.data
        transaction_id = data.get(NAMES.TRANSACTION_ID)
        amount = data.get(NAMES.AMOUNT)

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
            message='Error processing refund',
            code=RESPONSE_CODES.error,
            data={NAMES.ERROR: str(e)}
        )   