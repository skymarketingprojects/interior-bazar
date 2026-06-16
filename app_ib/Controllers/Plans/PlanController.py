from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.models import PlanQuery,BusinessPlan,ShopPlan,ArchitectPlan,CustomUser,Subscription,TransectionData
from app_ib.Utils.EngineConfig import ENTITY_TYPE
from app_ib.Controllers.Plans.Tasks.PlanTasks import PLAN_TASKS

from interior_notification.signals import planSignal
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from datetime import datetime
import asyncio

class PLAN_CONTROLLER:

    @classmethod
    async def CreateTransectionData(self,data):
        try:
            transection = await PLAN_TASKS.CreateTransectionData(data,paymentFor=NAMES.PLAN)
            if transection:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.transection_create_success,
                    code=RESPONSE_CODES.success,
                    data=transection
                )
        except Exception as e:
            pass
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.transection_create_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                }
            )
    @classmethod
    async def CreatePlan(self,payment_proof,data,user_ins):
        try:
            # Test Data
            plan_create_resp = await  PLAN_TASKS.CreatePlanTask(payment_proof=payment_proof, data=data, user_ins= user_ins)
            print(plan_create_resp)
            if plan_create_resp:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.plan_create_success,
                    code=RESPONSE_CODES.success,
                    data=plan_create_resp
                    )

            else:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.plan_create_error,
                    code=RESPONSE_CODES.error,
                    data={plan_create_resp})

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.plan_create_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })


    @classmethod
    async def VerifyPlan(self,data):
        try:
            is_plan_exist= await sync_to_async(PlanQuery.objects.filter(id=data.id).exists)()
            if(is_plan_exist):
                plan_ins=await sync_to_async(PlanQuery.objects.get)(id=data.id)
                pass

                verify_plan_response = await  PLAN_TASKS.VerifyPlanTask(plan_ins=plan_ins,data=data)
                pass

                if verify_plan_response:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.plan_verify_success,
                        code=RESPONSE_CODES.success,
                        data={NAMES.ID:plan_ins.id})

                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.plan_verify_errror,
                        code=RESPONSE_CODES.error,
                        data={NAMES.ID:plan_ins.id})
            else:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.plan_verify_errror,
                    code=RESPONSE_CODES.error,
                    data={})

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.plan_verify_errror,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })

    @classmethod
    async def CreateEntityPlan(self,planId,userId,transectionId):
        # Buy-before-entity: attach the purchased plan to the USER (entity FK NULL),
        # routing to the right plan model by Subscription.entityType. No entity is
        # required to exist — that hard dependency (user.user_business.id) is removed.
        try:
            user = await sync_to_async(CustomUser.objects.get)(id=userId)
            plan = await sync_to_async(Subscription.objects.get)(id=planId)
            entityType = plan.entityType or NAMES.BUSINESS
            if entityType == ENTITY_TYPE.SHOP:
                data = await PLAN_TASKS.CreateShopPlan(plan=plan,user=user,transectionId=transectionId)
            elif entityType == ENTITY_TYPE.ARCHITECT:
                data = await PLAN_TASKS.CreateArchitectPlan(plan=plan,user=user,transectionId=transectionId)
            else:
                data = await PLAN_TASKS.CreateBusinessPlan(plan=plan,user=user,transectionId=transectionId)
            if data:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.business_plan_create_success,
                    code=RESPONSE_CODES.success,
                    data=data
                    )
            else:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.business_plan_create_error,
                    code=RESPONSE_CODES.error,
                    data={})
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_plan_create_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })

    @classmethod
    async def ActivateEntityPlan(self,transectionId):
        # Find whichever entity plan model holds this transaction, activate it, and
        # flip the buyer to a seller (done inside the activate task).
        try:
            models_map = [
                (BusinessPlan, PLAN_TASKS.ActivateBusinessPlan, True),
                (ShopPlan, PLAN_TASKS.ActivateShopPlan, False),
                (ArchitectPlan, PLAN_TASKS.ActivateArchitectPlan, False),
            ]
            for Model, activateFn, fireSignal in models_map:
                exists = await sync_to_async(Model.objects.filter(transactionId=transectionId).exists)()
                if not exists:
                    continue
                planIns = await sync_to_async(Model.objects.get)(transactionId=transectionId)
                activated = await activateFn(planIns)
                if activated:
                    # planSignal is a Django Signal — dispatch via .send (sync) and ONLY
                    # when a Business is linked (the receiver reads instance.business; in
                    # the buy-first model the entity may not exist yet). Never let a
                    # notification failure fail activation.
                    if fireSignal and getattr(planIns, 'business', None):
                        try:
                            await sync_to_async(planSignal.send)(sender=planIns.__class__, instance=planIns)
                        except Exception:
                            pass
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.business_plan_activate_success,
                        code=RESPONSE_CODES.success,
                        data={NAMES.ID:planIns.id})
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.business_plan_activate_error,
                    code=RESPONSE_CODES.error,
                    data={NAMES.ID:planIns.id})
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_plan_activate_error,
                code=RESPONSE_CODES.error,
                data={})
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_plan_activate_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })
        
    # ── Upgrade (not downgrade) with prorated cost settlement (Prompt 9) ──
    _PLAN_MODELS = None  # lazy, set in _plan_model

    @classmethod
    def _plan_model(self, entityType):
        from app_ib.models import BusinessPlan, ShopPlan, ArchitectPlan
        return {
            ENTITY_TYPE.BUSINESS: BusinessPlan,
            ENTITY_TYPE.SHOP: ShopPlan,
            ENTITY_TYPE.ARCHITECT: ArchitectPlan,
        }.get(entityType, BusinessPlan)

    @classmethod
    def _aware(self, dt):
        if dt and timezone.is_naive(dt):
            return timezone.make_aware(dt, timezone.get_default_timezone())
        return dt

    @classmethod
    async def _get_active_plan(self, user, entityType):
        Model = self._plan_model(entityType)
        return await sync_to_async(
            lambda: Model.objects.select_related("plan").filter(user=user, isActive=True).order_by("-lastActivate").first()
        )()

    @classmethod
    async def PreviewUpgrade(self, user, entityType, targetPlanId):
        """Validate an upgrade and compute the prorated settlement. Rejects downgrade /
        same-tier and expired plans (expired → must buy fresh). Returns allowed + settleAmount."""
        try:
            plan = await self._get_active_plan(user, entityType)
            target = await sync_to_async(lambda: Subscription.objects.filter(id=targetPlanId).first())()
            if not plan or not plan.plan_id:
                return LocalResponse(response=RESPONSE_MESSAGES.error, message="No active plan to upgrade",
                                     code=RESPONSE_CODES.error, data={NAMES.ALLOWED: False, NAMES.REASON: "no_active_plan"})
            if not target:
                return LocalResponse(response=RESPONSE_MESSAGES.error, message="Invalid target plan",
                                     code=RESPONSE_CODES.error, data={NAMES.ALLOWED: False, NAMES.REASON: "invalid_target"})
            current_sub = await sync_to_async(lambda: plan.plan)()
            now = timezone.now()
            exp = self._aware(plan.expireDate)
            if exp and exp < now:
                return LocalResponse(response=RESPONSE_MESSAGES.error, message="Plan expired — buy fresh",
                                     code=RESPONSE_CODES.error, data={NAMES.ALLOWED: False, NAMES.REASON: "expired"})
            cur_tier = current_sub.tier or 0
            tgt_tier = target.tier or 0
            if tgt_tier <= cur_tier:
                return LocalResponse(response=RESPONSE_MESSAGES.error, message="Only upgrades to a higher tier are allowed",
                                     code=RESPONSE_CODES.error, data={NAMES.ALLOWED: False, NAMES.REASON: "not_higher_tier"})
            cur_amt = float(await MY_METHODS.formatAmount(plan.amount or current_sub.amount or "0"))
            tgt_amt = float(await MY_METHODS.formatAmount(target.amount or "0"))
            credit = 0.0
            last = self._aware(plan.lastActivate)
            if exp and last:
                total_days = max(1, (exp - last).days)
                remaining_days = max(0, (exp - now).days)
                credit = round(cur_amt * remaining_days / total_days, 2)
            settle = max(0.0, round(tgt_amt - credit, 2))
            return LocalResponse(response=RESPONSE_MESSAGES.success, message="Upgrade available",
                                 code=RESPONSE_CODES.success, data={
                NAMES.ALLOWED: True,
                NAMES.SETTLE_AMOUNT: settle,
                NAMES.ENTITY_TYPE: entityType,
                NAMES.TARGET_PLAN_ID: target.id,
                "currentTier": cur_tier, "targetTier": tgt_tier,
                "currentAmount": cur_amt, "targetAmount": tgt_amt, "creditApplied": credit,
                "planRowId": plan.id,
            })
        except Exception as e:
            return LocalResponse(response=RESPONSE_MESSAGES.error, message="Failed to preview upgrade",
                                 code=RESPONSE_CODES.error, data={NAMES.ALLOWED: False, NAMES.ERROR: str(e)})

    @classmethod
    async def StashUpgradeIntent(self, user, entityType, targetPlanId, transactionId):
        """Mark the user's active plan with the pending upgrade target + new txn, so the
        on-PAID handler can apply it. Stored in buyIntent: 'upgrade:<targetId>:<txn>'."""
        plan = await self._get_active_plan(user, entityType)
        if not plan:
            return False
        plan.buyIntent = f"upgrade:{targetPlanId}:{transactionId}"
        await sync_to_async(plan.save)()
        return True

    @classmethod
    async def ApplyUpgrade(self, transactionId):
        """On PAID: find the plan whose buyIntent stashes this txn, switch its plan FK to
        the target tier, recompute expireDate from the target duration, and clear the stash.
        It UPDATES the same row (not a new purchase)."""
        try:
            from app_ib.models import BusinessPlan, ShopPlan, ArchitectPlan
            suffix = f":{transactionId}"
            for Model in (BusinessPlan, ShopPlan, ArchitectPlan):
                planIns = await sync_to_async(
                    lambda M=Model: M.objects.filter(buyIntent__startswith="upgrade:", buyIntent__endswith=suffix).first()
                )()
                if not planIns:
                    continue
                try:
                    targetId = int(planIns.buyIntent.split(":")[1])
                except (IndexError, ValueError):
                    return False
                target = await sync_to_async(lambda: Subscription.objects.filter(id=targetId).first())()
                if not target:
                    return False
                planDuration = await MY_METHODS.parseDurationToDays(target.duration)
                today = await MY_METHODS.getCurrentDateTime()
                base = datetime(today.tm_year, today.tm_mon, today.tm_mday)
                planIns.plan = target
                planIns.amount = target.amount
                planIns.expireDate = base + relativedelta(months=planDuration)
                planIns.buyIntent = NAMES.WEBSITE
                await sync_to_async(planIns.save)()
                return True
            return False
        except Exception:
            return False

    @classmethod
    async def GetBusinessPlan(self,user):
        try:
            business = user.user_business
            plans = business.business_plan.all()
            plansData= {}
            for plan in plans:
                if plan.isActive == False:
                    continue
                data = await PLAN_TASKS.GetBusinessPlanData(businessPlan=plan)
                if data:
                    plansData=data
                if plan.isActive == True:
                    break

            if plansData:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.business_plan_fetch_success,
                    code=RESPONSE_CODES.success,
                    data=plansData
                    )

            else:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.business_plan_fetch_error,
                    code=RESPONSE_CODES.error,
                    data={})

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_plan_fetch_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })