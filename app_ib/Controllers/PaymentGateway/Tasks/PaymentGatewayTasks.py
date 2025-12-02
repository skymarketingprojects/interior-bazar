# app_ib/Controllers/PaymentGateway/Tasks/PaymentGatewayTasks.py
import uuid
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.models import CustomUser
from app_ib.Utils.CashfreeClient import CashfreeClientWrapper
from asgiref.sync import sync_to_async
from app_ib.Utils.Names import NAMES
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
                NAMES.TRANSACTION: transactionId,
                NAMES.USER_ID: userId,
                NAMES.AMOUNT: float(amount),
                NAMES.REDIRECT_URL: redirectUrl,
            }

            # await MY_METHODS.printStatus(f"Generated Cashfree transaction: {transaction_data}")
            return transaction_data

        except Exception as e:
            # await MY_METHODS.printStatus(f"Error in GenerateTransactionData: {e}")
            return None

    @classmethod
    async def CreateTransection( cls,user:CustomUser, redirectUrl: str,amount:float):
        try:
            transactionData = await cls.GenerateTransactionData(user.id, amount, redirectUrl)
            if not transactionData:
                return None
            
            transectionId = transactionData[NAMES.TRANSACTION]
            # Prepare payload for Cashfree REST API
            phone = ""
            try:
                phone = await MY_METHODS.formatPhone(country_code=str(user.user_profile.countryCode),phone=str(user.user_profile.phone))
            except Exception as e:
                phone = ""
            # await MY_METHODS.printStatus(f"amount in CreateTransection: {amount}, phone: {phone}")
            if phone == "":
                return None
            
            payload = {
                NAMES.ORDER_ID: transectionId,
                NAMES.ORDER_AMOUNT: float(amount),
                NAMES.ORDER_CURRENCY: NAMES.INR,
                NAMES.CUSTOMER_DETAILS: {
                    NAMES.CUSTOMER_ID: str(user.id),
                    NAMES.CUSTOMER_PHONE: phone,
                    NAMES.CUSTOMER_EMAIL: str(user.user_profile.email),
                },
                NAMES.ORDER_META: {
                    NAMES.RETURN_URL: f"{transactionData[NAMES.REDIRECT_URL]}?transactionId={transectionId}"
                },
            }

            response_data = await sync_to_async(CashfreeClientWrapper.create_order)(payload)
            # await MY_METHODS.printStatus(f"Cashfree Create Order Response: {response_data}")
            return response_data, transactionData
        except Exception as e:
            # await MY_METHODS.printStatus(f"Error in CreateTransection: {e}")
            return None