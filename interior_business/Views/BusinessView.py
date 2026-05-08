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
from adrf.views import APIView
from django.views.decorators.csrf import csrf_exempt
from app_ib.Utils.Names import NAMES
from app_ib.models import CustomUser


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
async def CreateBusinessView(request):
    try:
        # Convert request.data to dot notation object
        pass
        data = MY_METHODS.json_to_object(request.data)
        user_ins = request.user

        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(BUSS_CONTROLLER.CreateBusiness(user_ins=user_ins, data=data))
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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def UpdateBusinessView(request):
    try:
        # Convert request.data to dot notation object
        data = MY_METHODS.json_to_object(request.data)
        user_ins = request.user

        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(BUSS_CONTROLLER.UpdateeBusiness(user_ins=user_ins, data=data))
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
async def GetBusinessByIdView(request,id):
    try:
        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(BUSS_CONTROLLER.GetBusinessById(id=id))
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
async def GetBusinessByUser(request):
    try:
        user_ins:CustomUser = request.user
        business = user_ins.user_business
        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(BUSS_CONTROLLER.GetBusinessById(id=business.id))
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
async def GetAllBusinessTypesView(request):
    try:
        final_response = await BUSS_CONTROLLER.GetAllBusinessTypes()
        return ServerResponse(response=final_response.response, code=final_response.code, message=final_response.message, data=final_response.data)
    except Exception as e:
        return ServerResponse(response=RESPONSE_MESSAGES.error, message=RESPONSE_MESSAGES.business_type_fetch_error, code=RESPONSE_CODES.error, data={NAMES.ERROR: str(e)})

@api_view(['GET'])
async def GetAllBusinessTabView(request):
    try:
        final_response = await BUSS_CONTROLLER.GetAllBusinessTab()
        return ServerResponse(response=final_response.response, code=final_response.code, message=final_response.message, data=final_response.data)
    except Exception as e:
        return ServerResponse(response=RESPONSE_MESSAGES.error, message=RESPONSE_MESSAGES.business_category_fetch_error, code=RESPONSE_CODES.error, data={NAMES.ERROR: str(e)})

@api_view(['GET'])
async def GetAllBusinessCategoriesView(request):
    try:
        trending = request.query_params.get('trending', False)
        query = request.query_params.get('query', None)
        final_response = await BUSS_CONTROLLER.GetAllBusinessCategories(trending=trending, query=query)
        return ServerResponse(response=final_response.response, code=final_response.code, message=final_response.message, data=final_response.data)
    except Exception as e:
        return ServerResponse(response=RESPONSE_MESSAGES.error, message=RESPONSE_MESSAGES.business_category_fetch_error, code=RESPONSE_CODES.error, data={NAMES.ERROR: str(e)})

@api_view(['GET'])
async def GetAllBusinessSegmentsByTypeView(request, typeId):
    try:
        query = request.query_params.get('query', None)
        final_response = await BUSS_CONTROLLER.GetBusinessSegmentsByType(typeId=typeId, query=query)
        return ServerResponse(response=final_response.response, code=final_response.code, message=final_response.message, data=final_response.data)
    except Exception as e:
        return ServerResponse(response=RESPONSE_MESSAGES.error, message=RESPONSE_MESSAGES.business_category_fetch_error, code=RESPONSE_CODES.error, data={NAMES.ERROR: str(e)})

@api_view(['GET'])
async def GetExploreSectionsView(request):
    try:
        final_response = await BUSS_CONTROLLER.GetExploreSections()
        return ServerResponse(response=final_response.response, code=final_response.code, message=final_response.message, data=final_response.data)
    except Exception as e:
        return ServerResponse(response=RESPONSE_MESSAGES.error, message=RESPONSE_MESSAGES.business_category_fetch_error, code=RESPONSE_CODES.error, data={NAMES.ERROR: str(e)})

@api_view(['GET'])
async def GetBusinessHeaderView(request):
    try:
        # Call Auth Controller to Create User
        final_response = await BUSS_CONTROLLER.GetBusinessHeader()
        pass

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        pass
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.business_header_fetch_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })

class BusinessBannerView(APIView):
    permission_classes = [IsAuthenticated]
    async def post(self, request):
        try:
            # Convert request.data to dot notation object
            data = MY_METHODS.json_to_object(request.data)
            user = request.user

            # Call Auth Controller to Create User
            final_response = await BUSS_CONTROLLER.UpdateBusinessBanner(business_ins=user.user_business, data=data)
            pass

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
    async def get(self, request):
        try:
            # Call Auth Controller to Create User
            final_response = await BUSS_CONTROLLER.GetBusinessBanner(business_ins=request.user.user_business)
            pass

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