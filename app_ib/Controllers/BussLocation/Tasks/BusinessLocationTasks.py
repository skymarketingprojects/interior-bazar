from app_ib.models import Business
from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.models import Location, Business
from app_ib.Utils.MyMethods import MY_METHODS

class BUSS_LOC_TASK:

    @classmethod
    async def CreateBusinessLocTask(self, business_ins, data):
        try:
            business_loc_ins = Location()
            business_loc_ins.business=business_ins
            business_loc_ins.pin_code=data.pin_code
            business_loc_ins.city=data.city
            business_loc_ins.state=data.state
            business_loc_ins.country=data.country
            business_loc_ins.location_link=data.location_link
            await sync_to_async(business_loc_ins.save)()
            return True
            
        except Exception as e:
            await MY_METHODS.printStatus(f'Error in CreateBusinessLocTask {e}')
            return None

    @classmethod
    async def UpdateBusinessLocTask(self,business_loc_ins, data):
        try:
            business_loc_ins.pin_code=data.pin_code
            business_loc_ins.city=data.city
            business_loc_ins.state=data.state
            business_loc_ins.country=data.country
            business_loc_ins.location_link=data.location_link
            await sync_to_async(business_loc_ins.save)()
            return True
            
        except Exception as e:
            await MY_METHODS.printStatus(f'Error in UpdateBusinessLocTask {e}')
            return None

    @classmethod
    async def GetBusinessLocTask(self,business_loc_ins):
        try:
            business_loc_data={
                'pin_code':business_loc_ins.pin_code,
                'city':business_loc_ins.city,
                'state':business_loc_ins.state,
                'country':business_loc_ins.country,
                'location_link':business_loc_ins.location_link,
                'id':business_loc_ins.pk,
            }
            return business_loc_data
            
        except Exception as e:
            await MY_METHODS.printStatus(f'Error in GetBusinessLocTask {e}')
            return None
