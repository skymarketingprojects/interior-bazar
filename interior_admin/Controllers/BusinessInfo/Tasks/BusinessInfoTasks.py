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
            plan = business.business_plan.all()
            if plan:
                plan = plan.first()
                plan = plan.services
            else:
                plan = None

            data = {
                'name': business.name,
                "joinAt": business.timestamp.strftime("%d-%m-%Y"),
                "id": business.id,
                "plan": plan,
                "assignedLeads": assignLeads,
                "platformLeads": platformLeads,
                "totalLeads":totalLeads
            }
            return data
        except Exception as e:
            await MY_METHODS.printStatus(f"Error in GetBusinessInfo: {e}")
            return None
