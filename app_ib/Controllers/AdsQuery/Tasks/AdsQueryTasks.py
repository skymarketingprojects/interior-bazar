from asgiref.sync import sync_to_async
from app_ib.models import LeadQuery
from app_ib.Utils.MyMethods import MY_METHODS

class ADS_QUERY_TASKS:
    @classmethod
    async def CreateAdsQueryTask(self,data):
        try:
            await MY_METHODS.printStatus(f'data {data}')
            lead_query_ins = LeadQuery()
            lead_query_ins.phone= data.phone    
            lead_query_ins.interested= data.interested            
            await sync_to_async(lead_query_ins.save)()
            data = {
                'id':lead_query_ins.pk
            }
            return data
            
        except Exception as e:
            await MY_METHODS.printStatus(f'Error in CreateAdsQueryTask {e}')
            return None
  
    @classmethod
    async def VerifyAdsQueryTask(self, lead_query_ins, data):
        try:
            lead_query_ins.name= data.name
            lead_query_ins.email= data.email         
            lead_query_ins.query= data.query
            lead_query_ins.city= data.city
            lead_query_ins.country= data.country            
            await sync_to_async(lead_query_ins.save)()
            return True
            
        except Exception as e:
            await MY_METHODS.printStatus(f'Error in VerifyAdsQueryTask {e}')
            return None
