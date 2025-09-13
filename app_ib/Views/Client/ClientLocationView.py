import asyncio
from adrf.decorators import api_view
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Controllers.ClientLocation.ClientLocationController import CLIENT_LOCATION_CONTROLLER


@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def CreateOrUpdateClientLocationView(request):
    try:
        # Convert request.data to dot notation object
        data = MY_METHODS.json_to_object(request.data)
        user_ins = request.user
        await MY_METHODS.printStatus(f'user_ins {user_ins}')
        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(
            CLIENT_LOCATION_CONTROLLER.CreateOrUpdateClientLocation(user_ins=user_ins, data=data))
        await MY_METHODS.printStatus(f'final_response {final_response}')
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
            message=RESPONSE_MESSAGES.user_register_error,
            code=RESPONSE_CODES.error,
            data={
                'error': str(e)
            })


@api_view(['GET'])
async def GetClientLocationByIDView(request,id):
    try:
        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(CLIENT_LOCATION_CONTROLLER.GetClientLocByUserIns(id=id))
        
        await MY_METHODS.printStatus(f'final_response {final_response}')
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
            message=RESPONSE_MESSAGES.client_register_error,
            code=RESPONSE_CODES.error,
            data={
                'error': str(e)
            })