from asgiref.sync import sync_to_async
from app_ib.models import Location, Business,Country,State
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.Names import NAMES

class CLIENT_LOC_TASKS:

    @classmethod
    async def CreateClientLocTask(self, user_ins, data):
        try:
            state = await sync_to_async(State.objects.filter(id=data.state.id).first)()
            country = await sync_to_async(Country.objects.filter(id=data.country.id).first)()
            client_loc_ins = Location()
            client_loc_ins.user=user_ins
            client_loc_ins.pin_code=data.pin_code
            client_loc_ins.city=data.city
            # client_loc_ins.state=data.state
            # client_loc_ins.country=data.country
            client_loc_ins.locationState=state
            client_loc_ins.locationCountry=country
            client_loc_ins.location_link=data.location_link
            await sync_to_async(client_loc_ins.save)()
            return True
            
        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in CreateClientLocTask {e}')
            return None


    @classmethod
    async def UpdateClientLocTask(self,client_loc_ins:Location, data):
        try:
            state = await sync_to_async(State.objects.filter(id=data.state.id).first)()
            country = await sync_to_async(Country.objects.filter(id=data.country.id).first)()
            client_loc_ins.locationState=state
            client_loc_ins.locationCountry=country
            client_loc_ins.pin_code=data.pin_code
            client_loc_ins.city=data.city
            # client_loc_ins.state=data.state
            # client_loc_ins.country=data.country
            client_loc_ins.location_link=data.location_link
            await sync_to_async(client_loc_ins.save)()
            return True
            
        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in UpdateClientLocTask {e}')
            return None


    @classmethod
    async def GetClientLocTask(self,client_loc_ins:Location):
        try:
            client_loc_data={
                NAMES.PINCODE:client_loc_ins.pin_code,
                NAMES.CITY:client_loc_ins.city,
                NAMES.STATE:client_loc_ins.locationState.name if client_loc_ins.locationState else client_loc_ins.state,
                NAMES.COUNTRY:client_loc_ins.locationCountry.name if client_loc_ins.locationCountry else client_loc_ins.country,
                NAMES.LOCATION_LINK:client_loc_ins.location_link,
                NAMES.ID:client_loc_ins.pk,
            }
            return client_loc_data
            
        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in GetClientLocTask {e}')
            return None
