import asyncio
from app_ib.Utils.MyMethods import MY_METHODS
from django.http import JsonResponse
from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES
from app_ib.Controllers.AdsQuery.AdsQueryController import ADS_QUERY_CONTROLLER
from app_ib.models import UserProfile,CustomUser,Location

@api_view(['POST'])
async def CreateAdsQueryView(request):
    try:
        # await MY_METHODS.printStatus(f'Request Data: {request.data}')
        user = None
        reqdata = request.data
        if request.user.is_authenticated:
            user:CustomUser = request.user
            userProf:UserProfile = user.user_profile
            reqdata['phone']=userProf.phone
            reqdata['email']=userProf.email
            location = None
            if user.type == NAMES.BUSINESS:
                location:Location= user.user_business.business_location
            else:
                location:Location= user.user_location
            reqdata['city']=location.city
            reqdata['state']=location.locationState.name
            reqdata['country']=location.locationCountry.name
        # Convert request.data to dot notation object
        data = MY_METHODS.json_to_object(reqdata)
        
        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(ADS_QUERY_CONTROLLER.CreateAdsQuery(data=data,user=user))
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        # print(f'Error: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.ads_query_generate_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })


@api_view(['POST'])
async def VerifyAdsQueryView(request):
    try:
        # Convert request.data to dot notation object
        data = MY_METHODS.json_to_object(request.data)
        
        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(ADS_QUERY_CONTROLLER.VerifyAdsQuery(data=data))
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        # print(f'Error: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.quate_generate_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })
