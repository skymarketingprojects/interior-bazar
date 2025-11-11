from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Controllers.Business.Tasks.BusinessTasks import BUSS_TASK
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.models import Location, Business,Country,State
from app_ib.Controllers.BussLocation.Tasks.BusinessLocationTasks import BUSS_LOC_TASK
from app_ib.Utils.Names import NAMES

class BUSS_LOCATION_CONTROLLER:
  
    @classmethod
    async def CreateOrUpdateBusinessLocation(self, user_ins, data):
        try:
            business_ins = None
            business_loc_ins= None

            is_business_exist = await sync_to_async(Business.objects.filter(user=user_ins).exists)()
            #await MY_METHODS.printStatus(f'is_business_exist {is_business_exist}')

            if(is_business_exist):
                 business_ins = await sync_to_async(Business.objects.get)(user=user_ins)

            # Check if business already exist
            is_business_loc_exist = await sync_to_async(Location.objects.filter(business=business_ins).exists)()
            #await MY_METHODS.printStatus(f'is_business_loc_exist {is_business_loc_exist}')

            if is_business_loc_exist:
                business_loc_ins = await sync_to_async(Location.objects.get)(business=business_ins)
                #await MY_METHODS.printStatus(f'update business location')
                update_resp = await BUSS_LOC_TASK.UpdateBusinessLocTask(
                    business_loc_ins=business_loc_ins, data=data)
                if update_resp:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.business_loc_update_success,
                        code=RESPONSE_CODES.success,
                        data={})
                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.business_loc_update_error,
                        code=RESPONSE_CODES.error,
                        data={})

            else:
                #await MY_METHODS.printStatus(f'create business location')
                create_resp = await BUSS_LOC_TASK.CreateBusinessLocTask(
                    business_ins=business_ins, data=data)
                if create_resp:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.business_loc_create_success,
                        code=RESPONSE_CODES.success,
                        data={})
                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.business_loc_create_error,
                        code=RESPONSE_CODES.error,
                        data={})
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_register_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })

    @classmethod
    async def GetBuisnessLocByBusinessID(self,id):
        try:
            business_ins = None
            business_loc_ins= None

            is_business_exist = await sync_to_async(Business.objects.filter(pk=id).exists)()
            #await MY_METHODS.printStatus(f'is_business_exist {is_business_exist}')

            if(is_business_exist):
                 business_ins = await sync_to_async(Business.objects.get)(pk=id)

            # Check if business already exist
            is_business_loc_exist = await sync_to_async(Location.objects.filter(business=business_ins).exists)()

            if is_business_loc_exist:
                business_loc_ins = await sync_to_async(Location.objects.get)(business=business_ins)

                update_resp = await BUSS_LOC_TASK.GetBusinessLocTask(
                    business_loc_ins=business_loc_ins)
                if update_resp:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.business_loc_fetch_success,
                        code=RESPONSE_CODES.success,
                        data=update_resp)

                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.business_loc_fetch_error,
                        code=RESPONSE_CODES.error,
                        data={})

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_loc_fetch_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })

    @classmethod
    async def GetCountryList(self):
        try:
            countrys = await sync_to_async(Country.objects.all)()
            countryListData = []
            for country in countrys:
                countryListData.append(await BUSS_LOC_TASK.GetCountryDataTask(country=country))
            if countryListData:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.country_list_fetch_success,
                    code=RESPONSE_CODES.success,
                    data=countryListData)
            else:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.country_list_fetch_error,
                    code=RESPONSE_CODES.error,
                    data={})

        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in GetCountryList {e}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.country_list_fetch_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })
    @classmethod
    async def GetStateListByCountry(self,countryId):
        try:
            states = await sync_to_async(State.objects.filter(country__id=countryId).all)()
            stateListData = []
            for state in states:
                stateListData.append(await BUSS_LOC_TASK.GetStateDataTask(state=state))
            if stateListData:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.country_list_fetch_success,
                    code=RESPONSE_CODES.success,
                    data=stateListData)
            else:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.country_list_fetch_error,
                    code=RESPONSE_CODES.error,
                    data={})

        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in GetStateListByCountry {e}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.country_list_fetch_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })