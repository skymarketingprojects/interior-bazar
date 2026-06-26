from asgiref.sync import sync_to_async
from app_ib.models import PlanQuery,BusinessPlan,ShopPlan,ArchitectPlan,AutomationPlan,Business,CustomUser,Subscription,TransectionData
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.EngineConfig import ENTITY_TYPE, PLAN_STATUS
from dateutil.relativedelta import relativedelta
from datetime import datetime
from django.utils import timezone
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
            pass
            return False
    @classmethod
    async def CreatePlanTask(self, payment_proof, user_ins, data):
        try:
            pass
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
            pass
            return None


    @classmethod
    async def VerifyPlanTask(self, plan_ins:PlanQuery,data):
        try:
            pass
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
            pass
            return None
        

    @classmethod
    async def _computeExpiry(self, plan:Subscription):
        today = await MY_METHODS.getCurrentDateTime()
        planDuration = await MY_METHODS.parseDurationToDays(plan.duration)
        today_date = timezone.make_aware(datetime(today.tm_year, today.tm_mon, today.tm_mday))
        return today_date + relativedelta(months=planDuration)

    @classmethod
    async def CreateBusinessPlan(self,plan:Subscription,user:CustomUser,transectionId):
        # Buy-before-entity: attach to the USER with business FK NULL (filled when
        # the Business is created in-dashboard later — Prompt 7).
        try:
            expiry_date = await self._computeExpiry(plan)
            businessPlanIns = BusinessPlan()
            businessPlanIns.user= user
            businessPlanIns.business= None
            businessPlanIns.plan= plan
            businessPlanIns.services= plan.services
            businessPlanIns.amount= plan.amount
            businessPlanIns.isActive= False
            businessPlanIns.transactionId= transectionId
            businessPlanIns.expireDate= expiry_date
            businessPlanIns.buyIntent = NAMES.WEBSITE
            await sync_to_async(businessPlanIns.save)()
            return await self.GetPlanData(businessPlanIns, ENTITY_TYPE.BUSINESS)
        except Exception as e:
            return None

    @classmethod
    async def CreateShopPlan(self,plan:Subscription,user:CustomUser,transectionId):
        try:
            expiry_date = await self._computeExpiry(plan)
            shopPlanIns = ShopPlan()
            shopPlanIns.user= user
            shopPlanIns.shop= None
            shopPlanIns.plan= plan
            shopPlanIns.services= plan.services
            shopPlanIns.amount= plan.amount
            shopPlanIns.isActive= False
            shopPlanIns.transactionId= transectionId
            shopPlanIns.expireDate= expiry_date
            shopPlanIns.buyIntent = NAMES.WEBSITE
            await sync_to_async(shopPlanIns.save)()
            return await self.GetPlanData(shopPlanIns, ENTITY_TYPE.SHOP)
        except Exception as e:
            return None

    @classmethod
    async def CreateArchitectPlan(self,plan:Subscription,user:CustomUser,transectionId):
        try:
            expiry_date = await self._computeExpiry(plan)
            archPlanIns = ArchitectPlan()
            archPlanIns.user= user
            archPlanIns.architect= None
            archPlanIns.plan= plan
            archPlanIns.services= plan.services
            archPlanIns.amount= plan.amount
            archPlanIns.isActive= False
            archPlanIns.transactionId= transectionId
            archPlanIns.expireDate= expiry_date
            archPlanIns.buyIntent = NAMES.WEBSITE
            await sync_to_async(archPlanIns.save)()
            return await self.GetPlanData(archPlanIns, ENTITY_TYPE.ARCHITECT)
        except Exception as e:
            return None

    @classmethod
    def _flipUserToSeller(self, planIns):
        # Activating ANY entity plan makes the buyer a seller (buy-first model):
        # this replaces the old entity-creation-time type flip.
        user = getattr(planIns, 'user', None)
        if user is None:
            business = getattr(planIns, 'business', None)
            user = getattr(business, 'user', None) if business else None
        if user is not None and user.type != NAMES.BUSINESS:
            user.type = NAMES.BUSINESS
            user.save(update_fields=['type'])

    @classmethod
    async def _activatePlan(self, planIns):
        # status is the lifecycle source of truth; isActive is derived in model save().
        planIns.status = PLAN_STATUS.ACTIVE
        planIns.lastActivate = timezone.now()
        await sync_to_async(planIns.save)()
        await sync_to_async(self._flipUserToSeller)(planIns)
        return True

    @classmethod
    async def ActivateBusinessPlan(self,businessPlanIns:BusinessPlan):
        try:
            return await self._activatePlan(businessPlanIns)
        except Exception as e:
            return None

    @classmethod
    async def ActivateShopPlan(self,shopPlanIns:ShopPlan):
        try:
            return await self._activatePlan(shopPlanIns)
        except Exception as e:
            return None

    @classmethod
    async def ActivateArchitectPlan(self,archPlanIns:ArchitectPlan):
        try:
            return await self._activatePlan(archPlanIns)
        except Exception as e:
            return None

    @classmethod
    async def ActivateAutomationPlan(self,autoPlanIns:AutomationPlan):
        try:
            return await self._activatePlan(autoPlanIns)
        except Exception as e:
            return None

    @classmethod
    async def CreateAutomationPlan(self,plan:Subscription,user:CustomUser,transectionId):
        # Bundle plan: entity-less at purchase (all three entity FKs stay NULL until
        # the user creates each entity). Unlocks all three tabs via grantsEntityTypes.
        try:
            expiry_date = await self._computeExpiry(plan)
            autoPlanIns = AutomationPlan()
            autoPlanIns.user= user
            autoPlanIns.plan= plan
            autoPlanIns.services= plan.services
            autoPlanIns.amount= plan.amount
            autoPlanIns.status= PLAN_STATUS.PENDING
            autoPlanIns.transactionId= transectionId
            autoPlanIns.expireDate= expiry_date
            autoPlanIns.buyIntent = NAMES.WEBSITE
            await sync_to_async(autoPlanIns.save)()
            return await self.GetPlanData(autoPlanIns, ENTITY_TYPE.AUTOMATION)
        except Exception as e:
            return None

    @classmethod
    async def DeactivateBusinessPlan(self,businessPlanIns:BusinessPlan):
        try:
            businessPlanIns.status= PLAN_STATUS.EXPIRED
            await sync_to_async(businessPlanIns.save)()
            return True
        except Exception as e:
            pass
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
            pass
            return None

    @classmethod
    async def GetPlanData(self, planIns, entityType):
        # Generic history/card payload for any of the 3 entity plan models.
        # Caller must pass an instance whose .plan / entity FK are already loaded
        # (freshly created or select_related) to stay async-safe.
        try:
            if entityType == ENTITY_TYPE.SHOP:
                entity = getattr(planIns, 'shop', None); entityKey = NAMES.SHOP_ID
            elif entityType == ENTITY_TYPE.ARCHITECT:
                entity = getattr(planIns, 'architect', None); entityKey = NAMES.ARCHITECT_ID
            elif entityType == ENTITY_TYPE.AUTOMATION:
                # Bundle plan — entity-less; no single entityId to report.
                entity = None; entityKey = NAMES.BUSINESS_ID
            else:
                entity = getattr(planIns, 'business', None); entityKey = NAMES.BUSINESS_ID
            return {
                NAMES.ID: planIns.id,
                NAMES.ENTITY_TYPE: entityType,
                entityKey: entity.id if entity else None,
                NAMES.SERVICES: planIns.services,
                NAMES.AMOUNT: planIns.amount,
                NAMES.PLAN_ID: planIns.plan.id if planIns.plan else None,
                NAMES.PLAN_NAME: planIns.plan.title if planIns.plan else None,
                NAMES.ISACTIVE: planIns.isActive,
                NAMES.STATUS: planIns.status,
                NAMES.TRANSACTION: planIns.transactionId,
                NAMES.LAST_ACTIVATE: planIns.lastActivate.strftime(NAMES.YMD_FORMAT) if planIns.lastActivate else None,
                NAMES.EXPIRE_DATE: planIns.expireDate.strftime(NAMES.YMD_FORMAT) if planIns.expireDate else None,
                NAMES.TIMESTAMP: planIns.timestamp.strftime(NAMES.YMD_FORMAT) if planIns.timestamp else None,
                NAMES.UPDATED_AT: planIns.updatedAt.strftime(NAMES.YMD_FORMAT) if planIns.updatedAt else None,
            }
        except Exception as e:
            return None