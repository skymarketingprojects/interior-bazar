import asyncio
from adrf.decorators import api_view
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from interior_business.Controllers.BusinessProfile.BusinessProfileController import BUSS_PROFILE_CONTROLLER


@api_view(['GET'])
async def GetBusinessProfileForDisplayView(request, businessId = None):
    try:
        if businessId is None:
            businessId = request.user.user_business.id
        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(
            BUSS_PROFILE_CONTROLLER.GetBusinessProfileForDisplay(business_id=businessId))
        final_response = final_response[0]

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
            message=RESPONSE_MESSAGES.business_prof_fetch_error,
            code=RESPONSE_CODES.error,
            data={
                'error': str(e)
            })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def CreateOrUpdateBusinessProfileView(request):
    try:
        # Convert request.data to dot notation object
        data = MY_METHODS.json_to_object(request.data)
        user_ins = request.user

        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(
            BUSS_PROFILE_CONTROLLER.CreateOrUpdateBusinessProfile(user_ins=user_ins, data=data))
        final_response = final_response[0]
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
                'error': str(e)
            })

            
@api_view(['GET'])
async def GetBusinessProfileByBussIDView(request,id):
    try:
        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(
            BUSS_PROFILE_CONTROLLER.GetBuisnessProfByBusinessID(id=id))
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
            message=RESPONSE_MESSAGES.business_fetch_error,
            code=RESPONSE_CODES.error,
            data={
                'error': str(e)
            })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def CreateOrUpdatePrimaryImageView(request):
    try:
        # Get user instance
        user_ins = request.user
        primary_image = request.FILES.get('primary_image')  
        # await MY_METHODS.printStatus(f'primary image {primary_image}')

        # Call Auth Controller to Create User
        auth_resp = await  asyncio.gather(BUSS_PROFILE_CONTROLLER.CreateOrUpdatePrimaryImage(primary_image=primary_image,user_ins=user_ins))

        auth_resp = auth_resp[0]

        return ServerResponse(
            response=auth_resp.response,
            code=auth_resp.code,
            message=auth_resp.message,
            data=auth_resp.data)

    except Exception as e:
        # await MY_METHODS.printStatus(f'Error: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.user_profile_create_error,
            code=RESPONSE_CODES.error,
            data={
                'error': str(e)
            })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def CreateOrUpdateSecondaryImageView(request):
    try:
        # Get user instance
        user_ins = request.user
        secondary_image = request.FILES.get('secondary_image')  
        # await MY_METHODS.printStatus(f'secondary image  {secondary_image}')

        # Call Auth Controller to Create User
        auth_resp = await  asyncio.gather(BUSS_PROFILE_CONTROLLER.CreateOrUpdateSecondaryImage(secondary_image=secondary_image,user_ins=user_ins))
        auth_resp = auth_resp[0]

        return ServerResponse(
            response=auth_resp.response,
            code=auth_resp.code,
            message=auth_resp.message,
            data=auth_resp.data)

    except Exception as e:
        # await MY_METHODS.printStatus(f'Error: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.default_error,
            code=RESPONSE_CODES.error,
            data={
                'error': str(e)
            })