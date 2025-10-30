from ast import Try
import httpx
import asyncio
from django.http import JsonResponse
from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from app_ib.Utils.MyMethods import MY_METHODS
from interior_business.Controllers.Business.BusinessController import BUSS_CONTROLLER
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseCodes import RESPONSE_CODES


@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def CreateBusinessView(request):
    try:
        # Convert request.data to dot notation object
        data = MY_METHODS.json_to_object(request.data)
        user_ins = request.user

        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(BUSS_CONTROLLER.CreateBusiness(user_ins=user_ins, data=data))
        #await MY_METHODS.printStatus(f'final_response {final_response}')
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        # #await MY_METHODS.printStatus(f'Error: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.business_register_error,
            code=RESPONSE_CODES.error,
            data={
                'error': str(e)
            })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def UpdateBusinessView(request):
    try:
        # Convert request.data to dot notation object
        data = MY_METHODS.json_to_object(request.data)
        user_ins = request.user

        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(BUSS_CONTROLLER.UpdateeBusiness(user_ins=user_ins, data=data))
        #await MY_METHODS.printStatus(f'final_response {final_response}')
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        # #await MY_METHODS.printStatus(f'Error: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.business_register_error,
            code=RESPONSE_CODES.error,
            data={
                'error': str(e)
            })

@api_view(['GET'])
async def GetBusinessByIdView(request,id):
    try:
        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(BUSS_CONTROLLER.GetBusinessById(id=id))
        #await MY_METHODS.printStatus(f'final_response {final_response}')
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        # #await MY_METHODS.printStatus(f'Error: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.business_register_error,
            code=RESPONSE_CODES.error,
            data={
                'error': str(e)
            })

@api_view(['GET'])
async def GetBusinessByUser(request):
    try:
        user_ins = request.user
        business = user_ins.user_business
        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(BUSS_CONTROLLER.GetBusinessById(id=business.id))
        await MY_METHODS.printStatus(f'final_response {final_response}')
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        # #await MY_METHODS.printStatus(f'Error: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.business_register_error,
            code=RESPONSE_CODES.error,
            data={
                'error': str(e)
            })

@api_view(['GET'])
async def GetAllBusinessTypesView(request):
    try:
        # Call Auth Controller to Create User
        final_response = await BUSS_CONTROLLER.GetAllBusinessTypes()
        #await MY_METHODS.printStatus(f'final_response {final_response}')

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        # #await MY_METHODS.printStatus(f'Error: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.business_type_fetch_error,
            code=RESPONSE_CODES.error,
            data={
                'error': str(e)
            })
    
@api_view(['GET'])
async def GetAllBusinessCategoriesView(request):
    try:
        # Call Auth Controller to Create User
        final_response = await BUSS_CONTROLLER.GetAllBusinessCategories()
        #await MY_METHODS.printStatus(f'final_response {final_response}')

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        # #await MY_METHODS.printStatus(f'Error: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.business_category_fetch_error,
            code=RESPONSE_CODES.error,
            data={
                'error': str(e)
            })

@api_view(['GET'])
async def GetAllBusinessSegmentsByTypeView(request,typeId):
    try:
        # Call Auth Controller to Create User
        final_response = await BUSS_CONTROLLER.GetBusinessSegmentsByType(typeId=typeId)
        #await MY_METHODS.printStatus(f'final_response {final_response}')

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        # #await MY_METHODS.printStatus(f'Error: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.business_category_fetch_error,
            code=RESPONSE_CODES.error,
            data={
                'error': str(e)
            })