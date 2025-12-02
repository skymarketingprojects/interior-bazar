from asgiref.sync import sync_to_async
from app_ib.models import PlanQuery,BusinessPlan,Business,Subscription,TransectionData
from app_ib.Utils.MyMethods import MY_METHODS
from dateutil.relativedelta import relativedelta
from datetime import datetime
import time
from app_ib.Utils.Names import NAMES

class PLAN_TASKS:

    @classmethod
    async def CreateTransectionData(self,data,paymentFor:str):
        try:
            transection = TransectionData()
            transection.orderId= data.get(NAMES.CF_ORDER_ID,NAMES.EMPTY)
            transection.transactionId= data.get(NAMES.ORDER_ID,NAMES.EMPTY)
            transection.amount= data.get(NAMES.ORDER_AMOUNT,NAMES.EMPTY)
            transection.paymentFor= paymentFor
            transection.createdAt = data.get("created_at",NAMES.EMPTY)
            transection.expiryAt = data.get(NAMES.ORDER_EXPIRY_TIME,NAMES.EMPTY)
            transection.orderStatus= data.get(NAMES.ORDER_STATUS,NAMES.EMPTY)
            transection.paymentSessionId= data.get(NAMES.PAYMENT_SESSION_ID,NAMES.EMPTY)
            transection.save()
            return True
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in CreateTransectionData {e}')  
            return False
    @classmethod
    async def CreatePlanTask(self, payment_proof, user_ins, data):
        try:
            # await MY_METHODS.printStatus(f'Creating plan for user: {data}')
            plan_query = PlanQuery()
            plan_query.user= user_ins
            plan_query.plan= getattr(data, NAMES.PLAN, NAMES.EMPTY)
            plan_query.name= getattr(data, NAMES.NAME, NAMES.EMPTY)
            plan_query.email= getattr(data, NAMES.EMAIL, NAMES.EMPTY)
            plan_query.phone= getattr(data, NAMES.PHONE, NAMES.EMPTY)
            plan_query.state= getattr(data, NAMES.STATE, NAMES.EMPTY)
            plan_query.country= getattr(data, NAMES.COUNTRY, NAMES.EMPTY)
            # plan_query.address= data.address
            plan_query.stage= NAMES.PENDING
            plan_query.attachmentUrl= payment_proof
            plan_query.transactionId= getattr(data, NAMES.TRANSACTION, '')

            await sync_to_async(plan_query.save)()

            return {NAMES.ID:plan_query.id}

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in CreatePlanTask {e}')
            return None


    @classmethod
    async def VerifyPlanTask(self, plan_ins:PlanQuery,data):
        try:
            # await MY_METHODS.printStatus(f'Task {plan_ins}')
            plan_ins.stage= NAMES.CONFIRM
            plan_ins.plan= getattr(data, NAMES.PLAN, plan_ins.plan)
            plan_ins.name= getattr(data, NAMES.NAME, plan_ins.name)
            plan_ins.email= getattr(data, NAMES.EMAIL, plan_ins.email)
            plan_ins.phone= getattr(data, NAMES.PHONE, plan_ins.phone)
            plan_ins.state= getattr(data, NAMES.STATE, plan_ins.state)
            plan_ins.country= getattr(data, NAMES.COUNTRY, plan_ins.country)
            # plan_query.address= getattr(data, 'address', plan_ins.address)
            plan_ins.stage= getattr(data, NAMES.STAGE, plan_ins.stage)
            plan_ins.attachmentUrl= getattr(data, NAMES.ATTACHMENT_URL, plan_ins.attachmentUrl)
            plan_ins.transactionId= getattr(data, NAMES.TRANSACTION, plan_ins.transactionId)
            await sync_to_async(plan_ins.save)()
            return True
            
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in VerifyPlanTask {e}')
            return None
        

    @classmethod
    async def CreateBusinessPlan(self,plan:Subscription,businessId,transectionId):
        try:
            # await MY_METHODS.printStatus(f'Creating business plan for businessId: {businessId} with planId: {plan.id}')
            business = await sync_to_async(Business.objects.get)(id=businessId)
            today = await MY_METHODS.getCurrentDateTime()
            planDuration =  await MY_METHODS.parseDurationToDays(plan.duration)
            today_date = datetime(today.tm_year, today.tm_mon, today.tm_mday)
            expiry_date = today_date + relativedelta(months=planDuration)
            businessPlanIns = BusinessPlan()
            businessPlanIns.business= business
            businessPlanIns.plan= plan
            businessPlanIns.services= plan.services
            businessPlanIns.amount= plan.amount
            businessPlanIns.isActive= False
            businessPlanIns.transactionId= transectionId
            businessPlanIns.expireDate= expiry_date
            await sync_to_async(businessPlanIns.save)()

            data = await self.GetBusinessPlanData(businessPlanIns)
            return data
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in CreateBusinessPlan {e}')
            return None
        
    @classmethod
    async def ActivateBusinessPlan(self,businessPlanIns:BusinessPlan):
        try:

            businessPlanIns.isActive= True
            businessPlanIns.lastActivate= datetime.now()
            await sync_to_async(businessPlanIns.save)()
            return True
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in ActivateBusinessPlan {e}')
            return None
    
    @classmethod
    async def DeactivateBusinessPlan(self,businessPlanIns:BusinessPlan):
        try:
            businessPlanIns.isActive= False
            await sync_to_async(businessPlanIns.save)()
            return True
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in DeactivateBusinessPlan {e}')
            return None
    
    @classmethod
    async def GetBusinessPlanData(self,businessPlan:BusinessPlan):
        try:
            data = {
                NAMES.ID: businessPlan.id,
                NAMES.BUSINESS_ID: businessPlan.business.id if businessPlan.business else None,
                NAMES.SERVICES: businessPlan.services,
                NAMES.AMOUNT: businessPlan.amount,
                NAMES.PLAN_ID: businessPlan.plan.id if businessPlan.plan else None,
                NAMES.PLAN_NAME: businessPlan.plan.title if businessPlan.plan else None,
                NAMES.ISACTIVE: businessPlan.isActive,
                NAMES.TRANSACTION: businessPlan.transactionId,
                NAMES.LAST_ACTIVATE: businessPlan.lastActivate.strftime(NAMES.YMD_FORMAT) if businessPlan.lastActivate else None,
                NAMES.EXPIRE_DATE: businessPlan.expireDate.strftime(NAMES.YMD_FORMAT) if businessPlan.expireDate else None,
                NAMES.TIMESTAMP: businessPlan.timestamp.strftime(NAMES.YMD_FORMAT) if businessPlan.timestamp else None,
                NAMES.UPDATED_AT: businessPlan.updatedAt.strftime(NAMES.YMD_FORMAT) if businessPlan.updatedAt else None
            }
            return data
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in GetBusinessPlanData {e}')
            return None