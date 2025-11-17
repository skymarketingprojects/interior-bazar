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
from app_ib.Controllers.BussLocation.BussLocationController import BUSS_LOCATION_CONTROLLER


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
        # await MY_METHODS.printStatus(f'final_response {final_response}')
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        # await MY_METHODS.printStatus(f'Error: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.business_register_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })

@api_view(['GET'])
async def GetBusinessLocationByBussIDView(request,id):
    try:
        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(
            BUSS_LOCATION_CONTROLLER.GetBuisnessLocByBusinessID(id=id))
        # await MY_METHODS.printStatus(f'final_response {final_response}')
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        # await MY_METHODS.printStatus(f'Error: {e}')
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
        # Call Auth Controller to Create User
        final_response = await BUSS_LOCATION_CONTROLLER.GetCountryList()
        # await MY_METHODS.printStatus(f'final_response {final_response}')

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        # await MY_METHODS.printStatus(f'Error: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.business_register_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })
    
@api_view(['GET'])
async def GetStateListByCountryIDView(request,countryId):
    try:
        # Call Auth Controller to Create User
        final_response = await BUSS_LOCATION_CONTROLLER.GetStateListByCountry(countryId=countryId)
        # await MY_METHODS.printStatus(f'final_response {final_response}')

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        # await MY_METHODS.printStatus(f'Error: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.business_register_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })