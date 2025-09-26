from asgiref.sync import sync_to_async
from app_ib.models import Location, Business
from app_ib.Utils.MyMethods import MY_METHODS

class CLIENT_LOC_TASKS:

    @classmethod
    async def CreateClientLocTask(self, user_ins, data):
        try:
            client_loc_ins = Location()
            client_loc_ins.user=user_ins
            client_loc_ins.pin_code=data.pin_code
            client_loc_ins.city=data.city
            client_loc_ins.state=data.state
            client_loc_ins.country=data.country
            client_loc_ins.location_link=data.location_link
            await sync_to_async(client_loc_ins.save)()
            return True
            
        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in CreateClientLocTask {e}')
            return None


    @classmethod
    async def UpdateClientLocTask(self,client_loc_ins, data):
        try:
            client_loc_ins.pin_code=data.pin_code
            client_loc_ins.city=data.city
            client_loc_ins.state=data.state
            client_loc_ins.country=data.country
            client_loc_ins.location_link=data.location_link
            await sync_to_async(client_loc_ins.save)()
            return True
            
        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in UpdateClientLocTask {e}')
            return None


    @classmethod
    async def GetClientLocTask(self,client_loc_ins):
        try:
            client_loc_data={
                'pin_code':client_loc_ins.pin_code,
                'city':client_loc_ins.city,
                'state':client_loc_ins.state,
                'country':client_loc_ins.country,
                'location_link':client_loc_ins.location_link,
                'id':client_loc_ins.pk,
            }
            return client_loc_data
            
        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in GetClientLocTask {e}')
            return None
