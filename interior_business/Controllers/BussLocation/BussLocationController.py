from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.Names import NAMES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.models import Location, Business,Country,State
from interior_business.Controllers.BussLocation.Tasks.BusinessLocationTasks import BUSS_LOC_TASK
from django.core.cache import cache



class BUSS_LOCATION_CONTROLLER:
  
    @classmethod
    async def CreateOrUpdateBusinessLocation(self, user_ins, data):
        try:
            business_ins = None
            business_loc_ins= None

            is_business_exist = await sync_to_async(Business.objects.filter(user=user_ins).exists)()
            pass

            if(is_business_exist):
                 business_ins = await sync_to_async(Business.objects.get)(user=user_ins)

            # Check if business already exist
            is_business_loc_exist = await sync_to_async(Location.objects.filter(business=business_ins).exists)()
            pass

            if is_business_loc_exist:
                business_loc_ins = await sync_to_async(Location.objects.get)(business=business_ins)
                pass
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
                pass
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
    async def GetBuisnessLocByBusinessID(self,business):
        try:
            cache_key = f"business_location_{business.id}"
            cached_data = cache.get(cache_key)
            if cached_data:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.business_loc_fetch_success,
                    code=RESPONSE_CODES.success,
                    data=cached_data)

            business_loc_ins= None

            # Check if business already exist
            is_business_loc_exist = await sync_to_async(Location.objects.filter(business=business).exists)()

            if is_business_loc_exist:
                business_loc_ins = await sync_to_async(Location.objects.get)(business=business)

                update_resp = await BUSS_LOC_TASK.GetBusinessLocTask(
                    business_loc_ins=business_loc_ins)
                if update_resp:
                    cache.set(cache_key, update_resp, 3600)  # Cache for 1 hour
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
            cache_key = "all_countries_list"
            cached_data = cache.get(cache_key)
            if cached_data:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.country_list_fetch_success,
                    code=RESPONSE_CODES.success,
                    data=cached_data)

            countrys = await sync_to_async(Country.objects.all)()
            countryListData = []
            for country in countrys:
                countryListData.append(await BUSS_LOC_TASK.GetCountryDataTask(country=country))
            if countryListData:
                cache.set(cache_key, countryListData, 86400)  # Cache for 24 hours
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
            pass
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
            cache_key = f"states_list_{countryId}"
            cached_data = cache.get(cache_key)
            if cached_data:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.country_list_fetch_success,
                    code=RESPONSE_CODES.success,
                    data=cached_data)

            states = await sync_to_async(State.objects.filter(country__id=countryId).all)()
            stateListData = []
            for state in states:
                stateListData.append(await BUSS_LOC_TASK.GetStateDataTask(state=state))
            if stateListData:
                cache.set(cache_key, stateListData, 86400)  # Cache for 24 hours
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
            pass
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.country_list_fetch_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })