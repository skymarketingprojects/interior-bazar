# app_ib/Controllers/PaymentGateway/PaymentGatewayController.py
from uuid import uuid4
from asgiref.sync import sync_to_async
from django.conf import settings
import requests

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.Names import NAMES
from app_ib.Controllers.PaymentGateway.Tasks.PaymentGatewayTasks import PaymentGatewayTasks
from app_ib.Utils.CashfreeClient import CashfreeClientWrapper
from app_ib.Controllers.Plans.PlanController import PLAN_CONTROLLER
from interior_advertisement.Controllers.Ads.Tasks.AdsTasks import ADS_TASKS
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.models import Subscription
from interior_advertisement.models import AdCampaign,AdPayment,AdPaymentStatus
from interior_advertisement.Controllers.Ads.Tasks.AdsTasks import ADS_TASKS

class PaymentGatewayController:

    
   
    @classmethod
    async def InitiatePlanPayment(cls, data, user, redirectUrl):
        """
        Create a Cashfree payment order using REST API.
        """
        try:
            planId = data[NAMES.PLAN_ID]
            domain = redirectUrl

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
            response_data,transactionData = await PaymentGatewayTasks.CreateTransection(
                user=user,
                redirectUrl=domain,
                amount=amount
            )
            if response_data and response_data.get(NAMES.PAYMENT_SESSION_ID):
                payment_url = f"https://payments.cashfree.com/pgui/v2/checkout?payment_session_id={response_data['payment_session_id']}"

                # Create Business Plan
                businessPlan = await PLAN_CONTROLLER.CreateBusinessPlan(
                    planId=plan.id,
                    userId=user.id,
                    transectionId=transactionData[NAMES.TRANSACTION]
                )

                data = {
                    NAMES.PAYMENT_URL: payment_url,
                    NAMES.TRANSACTION: transactionData[NAMES.TRANSACTION],
                    NAMES.SESSION_ID: response_data.get(NAMES.PAYMENT_SESSION_ID),
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
                data={NAMES.ERROR: str(e)}
            )

    @classmethod
    async def InitiateADSPayment(cls, data, user, redirectUrl):
        try:
            campainId = data[NAMES.CAMPAIN_ID]
            domain = redirectUrl
            is_campain_exist = await sync_to_async(AdCampaign.objects.filter(id=campainId).exists)()
            if not is_campain_exist:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message="Invalid campaign ID",
                    code=RESPONSE_CODES.error,
                    data={}
                )

            campain = await sync_to_async(AdCampaign.objects.get)(id=campainId)
            campainAmount = await MY_METHODS.formatAmount(campain.placement.dailyPrice)

            days = campain.getDays()
            # await MY_METHODS.printStatus(f"campainAmount: {campainAmount}, days: {days}")
            amount = float(campainAmount) * days
            # return LocalResponse(
            #     response=RESPONSE_MESSAGES.error,
            #     message="Exception during advertisement payment initiation",
            #     code=RESPONSE_CODES.error,
            #     data={}
            # )
            
            response_data,transactionData = await PaymentGatewayTasks.CreateTransection(
                user=user,
                redirectUrl=domain,
                amount=amount
            )
            data[NAMES.AMOUNT] = amount
            data[NAMES.TRANSACTION] = transactionData[NAMES.TRANSACTION]

            adsresult = await ADS_TASKS.CreateAdPaymentTask(AdCampaignIns=campain,Data=data)
            
            # await MY_METHODS.printStatus(f"Advertisement payment initiated: {response_data}")
            payment_url = f"https://payments.cashfree.com/pgui/v2/checkout?payment_session_id={response_data['payment_session_id']}"

            data = {
                NAMES.PAYMENT_URL: payment_url,
                NAMES.TRANSACTION: transactionData[NAMES.TRANSACTION],
                NAMES.SESSION_ID: response_data.get(NAMES.PAYMENT_SESSION_ID),
            }

            if adsresult is None:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.warning,
                    message="Failed to create advertisement payment",
                    code=RESPONSE_CODES.warning,
                    data=data
                )
            
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message="Advertisement payment initiated successfully",
                code=RESPONSE_CODES.success,
                data=data
            )
        except Exception as e:
            # await MY_METHODS.printStatus(f"Error in InitiateADSPayment: {e}")
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Exception during advertisement payment initiation",
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )
    @classmethod
    async def CheckPaymentStatus(cls, transactionId,data):
        """
        Check payment status using Cashfree REST API.
        """
        try:
            response_data = await sync_to_async(CashfreeClientWrapper.fetch_order)(transactionId)
            status = response_data.get(NAMES.ORDER_STATUS, NAMES.CF_UNKNOWN)
            serviceType = data.get(NAMES.PAYMENT_FOR,NAMES.EMPTY)
            serviceActivated = None
            if serviceType == NAMES.PLAN and status == NAMES.CF_PAID:
                serviceActivated=await PLAN_CONTROLLER.ActivateBusinessPlan(transactionId)
            elif serviceType == NAMES.ADS and status == NAMES.CF_PAID:
                adPayment = await sync_to_async(AdPayment.objects.get)(transactionId=transactionId)
                data[NAMES.STATUS] = status.lower()
                serviceActivated=await ADS_TASKS.UpdateAdPaymentTask(AdPaymentIns=adPayment,Data=data)
            
            data = {
                NAMES.STATUS: status,
                NAMES.TRANSACTION: transactionId,
            }

            if serviceActivated is None and status == NAMES.CF_PAID:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.warning,
                    message="Failed to activate service after payment",
                    code=RESPONSE_CODES.warning,
                    data=data
                )
        
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
                data={NAMES.ERROR: str(e)}
            )

    @classmethod
    async def RefundTransaction(cls, transaction_id, amount):
        """
        Initiate refund via REST API.
        """
        try:
            refund_id = f"RFND-{uuid4().hex[:10]}"
            refund_payload = {
                NAMES.REFUND_AMOUNT: float(amount),
                NAMES.REFUND_ID: refund_id,
                NAMES.REFUND_NOTE: "Customer requested refund",
            }

            response_data = await sync_to_async(CashfreeClientWrapper.create_refund)(transaction_id, refund_payload)

            return LocalResponse(
                RESPONSE_MESSAGES.success,
                "Refund initiated",
                RESPONSE_CODES.success,
                {
                    NAMES.REFUND_ID: refund_id,
                    NAMES.STATUS: response_data.get(NAMES.REFUND_STATUS, NAMES.CF_UNKNOWN),
                    NAMES.RESPONSE: response_data,
                }
            )

        except Exception as e:
            return LocalResponse(
                RESPONSE_MESSAGES.error,
                "Refund failed",
                RESPONSE_CODES.error,
                {NAMES.ERROR: str(e)}
            )


