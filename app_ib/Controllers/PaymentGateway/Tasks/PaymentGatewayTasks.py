from django.urls import reverse
from app_ib.Utils.MyMethods import MY_METHODS
class PaymentGatewayTasks:

    @classmethod
    async def GenerateTransactionData(cls, userId: int, amount: int,domain:str):
        try:
            import uuid
            transactionId = f"TID-{uuid.uuid4().hex[:12].upper()}"

            redirectPath = f"{domain}/confirm-payment/{transactionId}/"
            # callbackPath = reverse("interior_bazzar:CheckPaymentStatusView", args=[transactionId])

            redirectUrl = redirectPath
            # callbackUrl = callbackPath

            transaction_data = {
                "transactionId": transactionId,
                "userId": userId,
                "amount": int(amount),
                "redirectUrl": redirectUrl,
                # "callbackUrl": callbackUrl
            }

            return transaction_data

        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in GenerateTransactionData: {e}')
            return None
