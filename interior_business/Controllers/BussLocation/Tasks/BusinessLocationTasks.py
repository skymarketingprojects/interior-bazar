from app_ib.models import Business,State,Country
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

            state = await sync_to_async(State.objects.filter(id=data.state.id).first)()
            country = await sync_to_async(Country.objects.filter(id=data.country.id).first)()
            business_loc_ins = Location()
            business_loc_ins.business=business_ins
            business_loc_ins.pin_code=data.pin_code
            business_loc_ins.city=data.city
            business_loc_ins.locationState=state
            business_loc_ins.locationCountry=country
            business_loc_ins.location_link=data.location_link
            await sync_to_async(business_loc_ins.save)()
            return True
            
        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in CreateBusinessLocTask {e}')
            return None

    @classmethod
    async def UpdateBusinessLocTask(self,business_loc_ins, data):
        try:
            state = await sync_to_async(State.objects.filter(id=data.state.id).first)()
            country = await sync_to_async(Country.objects.filter(id=data.country.id).first)()
            business_loc_ins.locationState=state
            business_loc_ins.locationCountry=country
            business_loc_ins.pin_code=data.pin_code
            business_loc_ins.city=data.city
            # business_loc_ins.state=data.state
            # business_loc_ins.country=data.country
            business_loc_ins.location_link=data.location_link
            await sync_to_async(business_loc_ins.save)()
            return True
            
        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in UpdateBusinessLocTask {e}')
            return None

    @classmethod
    async def GetBusinessLocTask(self,business_loc_ins):
        try:
            state = {
                "id": business_loc_ins.locationState.id,
                "name": business_loc_ins.locationState.name
            } if business_loc_ins.locationState else {
                "id": 1,
                "name": business_loc_ins.state
            }
            country = {
                "id": business_loc_ins.locationCountry.id,
                "name": business_loc_ins.locationCountry.name,
                "code": business_loc_ins.locationCountry.code
            } if business_loc_ins.locationCountry else {
                "id": 1,
                "name": business_loc_ins.country,
                "code":1
            }
            business_loc_data={
                'pin_code':business_loc_ins.pin_code,
                'city':business_loc_ins.city,
                'state':state,
                'country':country,
                'location_link':business_loc_ins.location_link,
                'id':business_loc_ins.pk,
            }
            return business_loc_data
            
        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in GetBusinessLocTask {e}')
            return None

    @classmethod
    async def GetCountryDataTask(self, country):
        try:
            countryData = {
                "id": country.id,
                "name": country.name,
                "code": country.code
            }
            return countryData
        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in GetCountryCodeTask {e}')
            return None
        
    @classmethod
    async def GetStateDataTask(self, state):
        try:
            stateData = {
                "id": state.id,
                "name": state.name
            }
            return stateData
        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in GetStateDataTask {e}')
            return None