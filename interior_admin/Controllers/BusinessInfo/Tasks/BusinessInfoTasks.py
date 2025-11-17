from asgiref.sync import sync_to_async
from app_ib.models import Business
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.Names import NAMES

class BUSINESS_INFO_TASKS:
    
    @classmethod
    async def GetBusinessInfo(cls, business):
        try:
            assignLeads = business.business_lead_query.count()
            platformLeads = 0
            totalLeads = assignLeads + platformLeads
            plans = business.business_plan.all()
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
                NAMES.NAME: business.business_name,
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
