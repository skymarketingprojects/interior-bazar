from asgiref.sync import sync_to_async
from app_ib.models import Business, BusinessPlan
from app_ib.Utils.Names import NAMES
from app_ib.decorators.ViewDecorator import taskExceptionHandler

from django.db.models import QuerySet
class BUSINESS_INFO_TASKS:
    
    @classmethod
    async def GetBusinessInfo(cls, business:Business):
        try:
            assignLeads = business.business_lead_query.count()
            platformLeads = 0
            totalLeads = assignLeads + platformLeads
            plans:QuerySet[BusinessPlan] = business.business_plan.all()
            planData = []
            if plans:
                # plans = plans.first()
                # plans = plans.service
                plans = plans.filter(isActive=True)
                for plan in plans:
                    plan = {
                        NAMES.ID: plan.id,
                        NAMES.NAME: plan.plan.title,
                        NAMES.EXPIRY_DATE: plan.expireDate.strftime(NAMES.DMY_FORMAT),
                        NAMES.ISACTIVE: plan.isActive,
                        NAMES.AMOUNT: plan.amount
                    }
                    planData.append(plan)

            data = {
                NAMES.NAME: business.businessName,
                NAMES.JOIN_AT: business.timestamp.strftime(NAMES.DMY_FORMAT),
                NAMES.ID: business.id,
                NAMES.PLAN: planData,
                NAMES.ASSIGNED_LEADS: assignLeads,
                NAMES.PLATFORM_LEADS: platformLeads,
                NAMES.TOTAL_LEADS:totalLeads
            }
            return data
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in GetBusinessInfo: {e}')
            return None

    @classmethod
    @taskExceptionHandler
    async def DeleteBusinessInfo(self, business:Business):
        await sync_to_async(business.delete)()
        return True,True
        