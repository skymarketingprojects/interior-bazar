from asgiref.sync import sync_to_async
from app_ib.models import FunnelForm

class FUNNEL_QUERY_TASKS:
    
    @classmethod
    async def CreateFunnelQuery(cls, data):
        try:
            funnel_form = FunnelForm(
                name = data.get('name',''),
                companyName = data.get('companyName',''),
                email = data.get('email',''),
                phone = data.get('phone',''),
                planType = data.get('planType',''),
                plan = data.get('plan',''),
                intrest = data.get('intrest',''),
                need = data.get('need','')
            )
            await sync_to_async(funnel_form.save)()
            return True, funnel_form
        except Exception as e:
            print("Error in CreateFunnelQuery:", e)
            return False, str(e)
        
    @classmethod
    async def GetFunnelQueries(cls,form):
        try:
            formData = {
                "id": form.id,
                "name": form.name,
                "companyName": form.companyName,
                "email": form.email,
                "phone": form.phone,
                "planType": form.planType,
                "plan": form.plan,
                "intrest": form.intrest,
                "need": form.need,
                "createdAt": form.timestamp
            }
            return True, formData
        except Exception as e:
            print("Error in GetFunnelQueries:", e)
            return False, str(e)