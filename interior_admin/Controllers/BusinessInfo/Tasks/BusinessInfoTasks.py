from asgiref.sync import sync_to_async
from app_ib.models import Business, BusinessPlan
from app_ib.Utils.Names import NAMES
from app_ib.decorators.ViewDecorator import taskExceptionHandler

from django.utils import timezone

from django.db.models import QuerySet
class BUSINESS_INFO_TASKS:
    
    @classmethod
    async def GetBusinessInfo(cls, business: Business):
        try:
            now = timezone.now()

            assignLeads = business.business_lead_query.count()
            platformLeads = 0
            totalLeads = assignLeads + platformLeads

            plans_qs: QuerySet[BusinessPlan] = (
                business.business_plan
                .select_related(NAMES.PLAN)
                .order_by(f"-{NAMES.TIMESTAMP}")
            )

            active_plan = (
                plans_qs
                .filter(
                    isActive=True,
                    expireDate__gte=now
                )
                .first()
            )

            last_plan = plans_qs.first()

            # PLAN TITLE RULE
            plan_name = (
                active_plan.plan.title
                if active_plan and active_plan.plan
                else "--"
            )

            # LAST PURCHASE RULE
            purchase_source = active_plan or last_plan

            last_purchase = (
                purchase_source.timestamp.strftime(NAMES.DMY_FORMAT)
                if purchase_source and purchase_source.timestamp
                else None
            )

            # EXPIRE RULE
            expire_source = active_plan or last_plan

            expire_date = (
                expire_source.expireDate.strftime(NAMES.DMY_FORMAT)
                if expire_source and expire_source.expireDate
                else None
            )

            data = {
                NAMES.ID: business.id,
                NAMES.NAME: business.businessName,

                # Created
                NAMES.JOIN_AT: business.timestamp.strftime(NAMES.DMY_FORMAT),

                # Plan section
                NAMES.PLAN: plan_name,
                NAMES.LAST_PURCHASE: last_purchase,
                NAMES.EXPIRE: expire_date,

                # Leads
                NAMES.LEADS_KOTA: 0,
                NAMES.ASSIGNED_LEADS: assignLeads,
                NAMES.PLATFORM_LEADS: platformLeads,
                NAMES.TOTAL_LEADS: totalLeads,
            }

            return data

        except Exception:
            return None

    @classmethod
    @taskExceptionHandler
    async def DeleteBusinessInfo(self, business:Business):
        await sync_to_async(business.delete)()
        return True,True
        