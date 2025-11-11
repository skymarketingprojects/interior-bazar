from asgiref.sync import sync_to_async
from app_ib.models import FunnelForm
from app_ib.Utils.Names import NAMES
class FUNNEL_QUERY_TASKS:
    
    @classmethod
    async def CreateFunnelQuery(cls, data):
        try:
            funnel_form = FunnelForm(
                name = data.get(NAMES.NAME,NAMES.EMPTY),
                companyName = data.get(NAMES.COMPANY_NAME,NAMES.EMPTY),
                email = data.get(NAMES.EMAIL,NAMES.EMPTY),
                phone = data.get(NAMES.PHONE,NAMES.EMPTY),
                planType = data.get(NAMES.PLAN_TYPE,NAMES.EMPTY),
                plan = data.get(NAMES.PLAN,NAMES.EMPTY),
                intrest = data.get(NAMES.INTREST,NAMES.EMPTY),
                need = data.get(NAMES.NEED,NAMES.EMPTY)
            )
            await sync_to_async(funnel_form.save)()
            return True, funnel_form
        except Exception as e:
            print('Error in CreateFunnelQuery:', e)
            return False, str(e)
        
    @classmethod
    async def GetFunnelQueries(cls,form):
        try:
            formData = {
                NAMES.ID: form.id,
                NAMES.NAME: form.name,
                NAMES.COMPANY_NAME: form.companyName,
                NAMES.EMAIL: form.email,
                NAMES.PHONE: form.phone,
                NAMES.PLAN_TYPE: form.planType,
                NAMES.PLAN: form.plan,
                NAMES.INTREST: form.intrest,
                NAMES.NEED: form.need,
                NAMES.CREATED_AT: form.timestamp
            }
            return True, formData
        except Exception as e:
            print('Error in GetFunnelQueries:', e)
            return False, str(e)