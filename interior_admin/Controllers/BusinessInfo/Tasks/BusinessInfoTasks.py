from asgiref.sync import sync_to_async
from app_ib.models import Business
from app_ib.Utils.MyMethods import MY_METHODS

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
                        "id": plan.id,
                        "name": plan.plan.title,
                        "expiryDate": plan.expireDate.strftime("%d-%m-%Y"),
                        "isActive": plan.isActive,
                        "amount": plan.amount
                    }
                    planData.append(plan)

            data = {
                'name': business.business_name,
                "joinAt": business.timestamp.strftime("%d-%m-%Y"),
                "id": business.id,
                "plan": planData,
                "assignedLeads": assignLeads,
                "platformLeads": platformLeads,
                "totalLeads":totalLeads
            }
            return data
        except Exception as e:
            #await MY_METHODS.printStatus(f"Error in GetBusinessInfo: {e}")
            return None
