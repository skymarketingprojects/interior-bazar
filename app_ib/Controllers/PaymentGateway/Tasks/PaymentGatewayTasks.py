# app_ib/Controllers/PaymentGateway/Tasks/PaymentGatewayTasks.py
import uuid
from app_ib.Utils.MyMethods import MY_METHODS

class PaymentGatewayTasks:

    @classmethod
    async def GenerateTransactionData(cls, userId: int, amount: float, domain: str):
        """
        Generates a unique transaction/order ID and associated redirect URLs
        for initiating a Cashfree payment.
        """
        try:
            transactionId = f"CFORD-{uuid.uuid4().hex[:12].upper()}"  # Cashfree-friendly ID

            redirectUrl = f"{domain}/"

            transaction_data = {
                "transactionId": transactionId,
                "userId": userId,
                "amount": float(amount),
                "redirectUrl": redirectUrl,
            }

            await MY_METHODS.printStatus(f"Generated Cashfree transaction: {transaction_data}")
            return transaction_data

        except Exception as e:
            await MY_METHODS.printStatus(f"Error in GenerateTransactionData: {e}")
            return None
