from app_ib.models import Business
from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse

class BUSS_TASK:

    @classmethod
    async def CreateBusinessTask(self, user_ins, data):
        try:
            business_ins = Business()
            business_ins.user=user_ins
            business_ins.business_name=data.business_name
            business_ins.segment=data.segment
            business_ins.catigory=data.catigory
            business_ins.whatsapp=data.whatsapp
            business_ins.gst=data.gst
            business_ins.since=data.since
            await sync_to_async(business_ins.save)()
            return True
            
        except Exception as e:
            print(f'Error in CreateBusinessTask {e}')
            return None


    @classmethod
    async def UpdateBusinessTask(self, business_ins, data):
        try:
            business_ins.business_name=data.business_name
            business_ins.segment=data.segment
            business_ins.catigory=data.catigory
            business_ins.whatsapp=data.whatsapp
            business_ins.gst=data.gst
            business_ins.since=data.since
            
            await sync_to_async(business_ins.save)()
            return True
            
        except Exception as e:
            print(f'Error in UpdateBusinessTask {e}')
            return None


    @classmethod
    async def GetBusinessInfo(self,id):
        try:
            business_ins = await sync_to_async(Business.objects.get)(pk=id)

            data = {
                'business_name': business_ins.business_name,
                'segment': business_ins.segment,
                'catigory': business_ins.catigory,
                'whatsapp': business_ins.whatsapp,
                'gst': business_ins.gst,
                'since': business_ins.since,
                'buss_id': business_ins.id
            }
            return data
            
        except Exception as e:
            print(f'Error in GetBusinessInfo {e}')
            return None