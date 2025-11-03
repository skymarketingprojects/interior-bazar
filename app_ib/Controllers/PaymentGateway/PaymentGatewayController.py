# app_ib/Controllers/PaymentGateway/PaymentGatewayController.py
from uuid import uuid4
from asgiref.sync import sync_to_async
from django.conf import settings
import requests

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Controllers.PaymentGateway.Tasks.PaymentGatewayTasks import PaymentGatewayTasks
from app_ib.Utils.CashfreeClient import CashfreeClientWrapper
from app_ib.Controllers.Plans.PlanController import PLAN_CONTROLLER
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.models import Subscription


class PaymentGatewayController:

    @classmethod
    async def InitiatePayment(cls, data, userId):
        """
        Create a Cashfree payment order using REST API.
        """
        try:
            planId = data['planId']
            domain = data['domain']

            is_plan_exist = await sync_to_async(Subscription.objects.filter(id=planId).exists)()
            if not is_plan_exist:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message="Invalid plan ID",
                    code=RESPONSE_CODES.error,
                    data={}
                )

            plan = await sync_to_async(Subscription.objects.get)(id=planId)
            planAmount = await MY_METHODS.formatAmount(plan.amount)
            amount = float(planAmount)

            # Generate transaction data
            transactionData = await PaymentGatewayTasks.GenerateTransactionData(userId, amount, domain)
            if not transactionData:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message="Failed to generate transaction data",
                    code=RESPONSE_CODES.error,
                    data={}
                )

            # Prepare payload for Cashfree REST API
            payload = {
                "order_id": transactionData["transactionId"],
                "order_amount": amount,
                "order_currency": "INR",
                "customer_details": {
                    "customer_id": str(userId),
                    "customer_phone": data.get("phone", "9999999999"),
                    "customer_email": data.get("email", "test@example.com"),
                },
                "order_meta": {
                    "return_url": f"{transactionData['redirectUrl']}?transactionId={{order_id}}"
                },
            }

            response_data = await sync_to_async(CashfreeClientWrapper.create_order)(payload)

            if response_data and response_data.get("payment_session_id"):
                payment_url = f"https://payments.cashfree.com/pgui/v2/checkout?payment_session_id={response_data['payment_session_id']}"

                # Create Business Plan
                businessPlan = await PLAN_CONTROLLER.CreateBusinessPlan(
                    planId=plan.id,
                    userId=userId,
                    transectionId=transactionData["transactionId"]
                )

                data = {
                    "paymentUrl": payment_url,
                    "transactionId": transactionData["transactionId"],
                    "se": response_data.get("payment_session_id"),
                }

                if businessPlan is None:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.warning,
                        message="Failed to create business plan",
                        code=RESPONSE_CODES.warning,
                        data=data
                    )

                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message="Payment initiated successfully",
                    code=RESPONSE_CODES.success,
                    data=data
                )
            else:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=f"Failed to create Cashfree order: {response_data}",
                    code=RESPONSE_CODES.error,
                    data={}
                )

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Exception during payment initiation",
                code=RESPONSE_CODES.error,
                data={"error": str(e)}
            )

    @classmethod
    async def CheckPaymentStatus(cls, transactionId):
        """
        Check payment status using Cashfree REST API.
        """
        try:
            response_data = await sync_to_async(CashfreeClientWrapper.fetch_order)(transactionId)
            status = response_data.get("order_status", "UNKNOWN")

            if status == "PAID":
                await PLAN_CONTROLLER.ActivateBusinessPlan(transactionId)

            data = {
                "status": status,
                "transactionId": transactionId,
            }

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message="Payment status fetched",
                code=RESPONSE_CODES.success,
                data=data
            )

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Failed to check payment status",
                code=RESPONSE_CODES.error,
                data={"error": str(e)}
            )

    @classmethod
    async def RefundTransaction(cls, transaction_id, amount):
        """
        Initiate refund via REST API.
        """
        try:
            refund_id = f"RFND-{uuid4().hex[:10]}"
            refund_payload = {
                "refund_amount": float(amount),
                "refund_id": refund_id,
                "refund_note": "Customer requested refund",
            }

            response_data = await sync_to_async(CashfreeClientWrapper.create_refund)(transaction_id, refund_payload)

            return LocalResponse(
                RESPONSE_MESSAGES.success,
                "Refund initiated",
                RESPONSE_CODES.success,
                {
                    "refund_id": refund_id,
                    "status": response_data.get("refund_status", "UNKNOWN"),
                    "response": response_data,
                }
            )

        except Exception as e:
            return LocalResponse(
                RESPONSE_MESSAGES.error,
                "Refund failed",
                RESPONSE_CODES.error,
                {"error": str(e)}
            )
