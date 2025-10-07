# app_ib/Controllers/PaymentGateway/PaymentGatewayController.py

from uuid import uuid4
from asgiref.sync import sync_to_async
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Controllers.PaymentGateway.Tasks.PaymentGatewayTasks import PaymentGatewayTasks
from app_ib.Utils.PhonePeClient import PhonePeClientWrapper
from phonepe.sdk.pg.payments.v2.models.request.standard_checkout_pay_request import StandardCheckoutPayRequest
from phonepe.sdk.pg.common.models.request.meta_info import MetaInfo
from phonepe.sdk.pg.common.models.request.refund_request import RefundRequest
from app_ib.Controllers.Plans.PlanController import PLAN_CONTROLLER
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.models import BusinessPlan, Subscription, Business
class PaymentGatewayController:

    @classmethod
    async def InitiatePayment(cls,data,userId):
        try:
            # #await MY_METHODS.printStatus(f"amount {data['amount']}")
            # amount = data["amount"]*100
            # #await MY_METHODS.printStatus(f"Initiating payment for user {userId} of amount {amount}")

            planId = data['planId']
            domain = data['domain']
            #await MY_METHODS.printStatus(f"plan id {planId}")

            is_plan_exist= await sync_to_async(Subscription.objects.filter(id=planId).exists)()
            #await MY_METHODS.printStatus(f"plan exist {is_plan_exist}")
            if not is_plan_exist:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message="Invalid plan ID",
                    code=RESPONSE_CODES.error,
                    data={}
                )
            plan = await sync_to_async(Subscription.objects.get)(id=planId)

            planAmount = await MY_METHODS.formatAmount(plan.amount)
            #await MY_METHODS.printStatus(f"plan amount {planAmount}")
            amount = planAmount * 100
            #await MY_METHODS.printStatus(f"amount {amount}")

            transactionData = await PaymentGatewayTasks.GenerateTransactionData(userId, amount,domain)
            if not transactionData:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message="Failed to generate transaction data",
                    code=RESPONSE_CODES.error,
                    data={}
                )

            # Setup meta info if needed (you can customize UDFs)
            meta_info = MetaInfo(
                udf1=str(userId),
                udf2="InteriorBazzar",
                udf3="v2"
            )

            # Build SDK payment request
            #await MY_METHODS.printStatus(f"transaction data {transactionData}")
            sdk_request = StandardCheckoutPayRequest.build_request(
                merchant_order_id=transactionData["transactionId"],
                amount= int(amount),
                redirect_url=transactionData["redirectUrl"],
                meta_info=meta_info
            )
            #await MY_METHODS.printStatus(f"sdk request {sdk_request}")

            # Get PhonePe client and send request
            client = PhonePeClientWrapper.get_client()
            sdk_response = client.pay(sdk_request)
            #await MY_METHODS.printStatus(f"sdk response {sdk_response}")

            if sdk_response and sdk_response.redirect_url:
                data={
                        "paymentUrl": sdk_response.redirect_url,
                        "redirectUrl": transactionData["redirectUrl"],
                        # "callbackUrl": transactionData["callbackUrl"],
                        "transactionId": transactionData["transactionId"]
                    }
                businessPlan = await PLAN_CONTROLLER.CreateBusinessPlan(planId=plan.id,userId = userId, transectionId= transactionData["transactionId"])
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
                    message="Failed to get redirect URL from PhonePe",
                    code=RESPONSE_CODES.error,
                    data={}
                )

        except Exception as e:
            await MY_METHODS.printStatus(f'Error in InitiatePayment: {e}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Exception during payment initiation",
                code=RESPONSE_CODES.error,
                data={"error": str(e)}
            )


    @classmethod
    async def CheckPaymentStatus(cls, transactionId):
        try:
            client = PhonePeClientWrapper.get_client()
            response = client.get_order_status(merchant_order_id=transactionId)
            if response.state == "COMPLETED":
                activate = await PLAN_CONTROLLER.ActivateBusinessPlan(transactionId)
            data={
                    "status": response.state,  # "COMPLETED", "PENDING", etc.
                    "transactionId": transactionId
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
        try:
            from uuid import uuid4
            refund_id = f"RFND-{uuid4().hex[:10]}"

            refund_request = RefundRequest.build_refund_request(
                merchant_refund_id=refund_id,
                original_merchant_order_id=transaction_id,
                amount=amount
            )

            client = PhonePeClientWrapper.get_client()
            response = client.refund(refund_request=refund_request)

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message="Refund initiated",
                code=RESPONSE_CODES.success,
                data={
                    "state": response.state.value,
                    "refund_id": refund_id
                }
            )
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Refund failed",
                code=RESPONSE_CODES.error,
                data={"error": str(e)}
            )
