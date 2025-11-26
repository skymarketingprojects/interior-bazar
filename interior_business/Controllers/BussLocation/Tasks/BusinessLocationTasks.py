from app_ib.models import Business,State,Country
from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.models import Location, Business
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.Names import NAMES

class BUSS_LOC_TASK:

    @classmethod
    async def CreateBusinessLocTask(self, business_ins, data):
        try:

            state = await sync_to_async(State.objects.filter(id=data.state.id).first)()
            country = await sync_to_async(Country.objects.filter(id=data.country.id).first)()
            business_loc_ins = Location()
            business_loc_ins.business=business_ins
            business_loc_ins.pinCode=data.pinCode
            business_loc_ins.city=data.city
            business_loc_ins.locationState=state
            business_loc_ins.locationCountry=country
            business_loc_ins.locationLink=data.gmbLink
            await sync_to_async(business_loc_ins.save)()
            return True
            
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in CreateBusinessLocTask {e}')
            return None

    @classmethod
    async def UpdateBusinessLocTask(self,business_loc_ins:Location, data):
        try:
            state = await sync_to_async(State.objects.filter(id=data.state.id).first)()
            country = await sync_to_async(Country.objects.filter(id=data.country.id).first)()
            business_loc_ins.locationState=state
            business_loc_ins.locationCountry=country
            business_loc_ins.pinCode=data.pinCode
            business_loc_ins.city=data.city
            # business_loc_ins.state=data.state
            # business_loc_ins.country=data.country
            business_loc_ins.locationLink=data.gmbLink
            await sync_to_async(business_loc_ins.save)()
            return True
            
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in UpdateBusinessLocTask {e}')
            return None

    @classmethod
    async def GetBusinessLocTask(self,business_loc_ins:Location):
        try:
            state = {
                NAMES.ID: business_loc_ins.locationState.id,
                NAMES.NAME: business_loc_ins.locationState.name
            } 
            country = {
                NAMES.ID: business_loc_ins.locationCountry.id,
                NAMES.NAME: business_loc_ins.locationCountry.name,
                NAMES.CODE: business_loc_ins.locationCountry.code
            }
            business_loc_data={
                NAMES.PINCODE:business_loc_ins.pinCode,
                NAMES.CITY:business_loc_ins.city,
                NAMES.STATE:state,
                NAMES.COUNTRY:country,
                NAMES.GMB_LINK:business_loc_ins.locationLink,
                NAMES.ID:business_loc_ins.pk,
            }
            return business_loc_data
            
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in GetBusinessLocTask {e}')
            return None

    @classmethod
    async def GetCountryDataTask(self, country:Country):
        try:
            countryData = {
                NAMES.ID: country.id,
                NAMES.NAME: country.name,
                NAMES.CODE: country.code
            }
            return countryData
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in GetCountryCodeTask {e}')
            return None
        
    @classmethod
    async def GetStateDataTask(self, state:State):
        try:
            stateData = {
                NAMES.ID: state.id,
                NAMES.NAME: state.name,
                NAMES.VALUE: state.value
            }
            return stateData
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in GetStateDataTask {e}')
            return None