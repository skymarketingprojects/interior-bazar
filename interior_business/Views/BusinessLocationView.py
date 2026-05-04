from ast import Try
import httpx
import asyncio
from django.http import JsonResponse
from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Controllers.Business.BusinessController import BUSS_CONTROLLER
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES
from interior_business.Controllers.BussLocation.BussLocationController import BUSS_LOCATION_CONTROLLER
from django.core.cache import cache

cache_get = sync_to_async(cache.get)
cache_set = sync_to_async(cache.set)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def CreateOrUpdateBusinessLocationView(request):
    try:
        # Convert request.data to dot notation object
        data = MY_METHODS.json_to_object(request.data)
        user_ins = request.user

        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(
            BUSS_LOCATION_CONTROLLER.CreateOrUpdateBusinessLocation(user_ins=user_ins, data=data))
        pass
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        pass
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.business_register_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def GetBusinessLocationView(request):
    try:
        
        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(
            BUSS_LOCATION_CONTROLLER.GetBuisnessLocByBusinessID(business = request.user.user_business))
        pass
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        pass
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.business_register_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })
    
@api_view(['GET'])
async def GetCountryListView(request):
    try:
        cached = await cache_get("cache:location:countries")
        if cached:
            return ServerResponse(**cached)
        final_response = await BUSS_LOCATION_CONTROLLER.GetCountryList()
        await cache_set("cache:location:countries", {'response': final_response.response, 'code': final_response.code, 'message': final_response.message, 'data': final_response.data}, timeout=604800)  # 7 days
        return ServerResponse(response=final_response.response, code=final_response.code, message=final_response.message, data=final_response.data)
    except Exception as e:
        return ServerResponse(response=RESPONSE_MESSAGES.error, message=RESPONSE_MESSAGES.business_register_error, code=RESPONSE_CODES.error, data={NAMES.ERROR: str(e)})
@api_view(['GET'])
async def GetStateListByCountryIDView(request, countryId):
    try:
        cache_key = f"cache:location:states:{countryId}"
        cached = await cache_get(cache_key)
        if cached:
            return ServerResponse(**cached)
        final_response = await BUSS_LOCATION_CONTROLLER.GetStateListByCountry(countryId=countryId)
        await cache_set(cache_key, {'response': final_response.response, 'code': final_response.code, 'message': final_response.message, 'data': final_response.data}, timeout=604800)  # 7 days
        return ServerResponse(response=final_response.response, code=final_response.code, message=final_response.message, data=final_response.data)
    except Exception as e:
        return ServerResponse(response=RESPONSE_MESSAGES.error, message=RESPONSE_MESSAGES.business_register_error, code=RESPONSE_CODES.error, data={NAMES.ERROR: str(e)})