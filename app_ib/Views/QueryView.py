from ast import Try
import httpx
import asyncio
from app_ib.Utils.MyMethods import MY_METHODS
from django.http import JsonResponse,HttpRequest
from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from app_ib.Controllers.Query.QueryController import LEAD_QUERY_CONTROLLER
from app_ib.Controllers.FunnelQuery.FunnelQueryController import FUNNEL_QUERY_CONTROLLER
from app_ib.models import UserProfile,CustomUser,Location
from app_ib.Controllers.Query.Validators.QueryValidators import leadQuerysData,leadData
from dateutil.parser import parse
from datetime import date

@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def GetQueryView(request):
    try:
        user = request.user
        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(LEAD_QUERY_CONTROLLER.GetQueries(user_ins=user))
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
            message=RESPONSE_MESSAGES.query_fetch_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })

@api_view(['POST'])
async def CreateQueryView(request):
    try:
        # await MY_METHODS.printStatus(f'Request Data: {request.data}')
        user = None
        reqdata:dict = request.data
        if request.user.is_authenticated:
            user = request.user
            userProf:UserProfile = user.user_profile

            reqdata['phone'] = reqdata.get('phone') or userProf.phone
            reqdata['email'] = reqdata.get('email') or userProf.email
            try:

                if user.type == NAMES.BUSINESS:
                    location:Location = user.user_business.business_location
                else:
                    location:Location = user.user_location

                reqdata['city']    = reqdata.get('city') or location.city
                reqdata['state']   = reqdata.get('state') or location.locationState.name
                reqdata['country'] = reqdata.get('country') or location.locationCountry.name
            except Exception as e:
                # await MY_METHODS.printStatus(f'Error in CreateQueryView {e}')
                pass
                
        # Convert request.data to dot notation object
        data = leadData(**reqdata)
        
        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(LEAD_QUERY_CONTROLLER.CreateLeadQuery(data=data,user=user))
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
            message=RESPONSE_MESSAGES.query_generate_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })


@api_view(['POST'])
# @permission_classes([IsAuthenticated])
async def UpdateQueryByIDView(request):
    try:
        user = None
        reqdata = request.data
        if request.user.is_authenticated:
            user = request.user
            userProf:UserProfile = user.user_profile

            reqdata['phone'] = reqdata.get('phone') or userProf.phone
            reqdata['email'] = reqdata.get('email') or userProf.email
            try:
                if user.type == NAMES.BUSINESS:
                    location:Location = user.user_business.business_location
                else:
                    location:Location = user.user_location

                reqdata['city']    = reqdata.get('city') or location.city
                reqdata['state']   = reqdata.get('state') or location.locationState.name
                reqdata['country'] = reqdata.get('country') or location.locationCountry.name
            except Exception as e:
                # await MY_METHODS.printStatus(f'Error in UpdateQueryByIDView {e}')
                pass
        # Convert request.data to dot notation object
        data= leadData(**reqdata)
        

        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(LEAD_QUERY_CONTROLLER.UpdateLeadQuery(data=data))
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        # await MY_METHODS.printStatus(f'Error: {str(e)}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.query_update_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def UpdateQueryStatusView(request):
    try:
        # Convert request.data to dot notation object
        data= MY_METHODS.json_to_object(request.data)
        user_ins= request.user 
    
        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(LEAD_QUERY_CONTROLLER.UpdateLeadQueryStatus(data=data))
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.query_update_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def UpdateQueryPriorityView(request):
    try:
        # Convert request.data to dot notation object
        data= MY_METHODS.json_to_object(request.data)
        user_ins= request.user 
    
        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(LEAD_QUERY_CONTROLLER.UpdateLeadQueryPriority(data=data))
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.query_update_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def UpdateQueryRemarkView(request):
    try:
        # Convert request.data to dot notation object
        data= MY_METHODS.json_to_object(request.data)
        user_ins= request.user 
    
        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(LEAD_QUERY_CONTROLLER.UpdateLeadQueryRemark(data=data))
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.query_update_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def GetQueryByID(request,id):
    try:
        # Convert request.data to dot notation object
        data= MY_METHODS.json_to_object(request.data)
        user_ins= request.user 

        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(LEAD_QUERY_CONTROLLER.GetQueryById(id=id))
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.query_fetch_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def GetQueryBusinessView(request:HttpRequest):
    try:
        user_ins= request.user
        status = request.GET.get('status')
        tag = request.GET.get('tag')
        priority = request.GET.get('priority')
        leadFor = request.GET.get('leadFor')
        fromDate = request.GET.get('dateFrom')
        toDate = request.GET.get('dateTo')
        

        queryParams= leadQuerysData(
            status=status,
            tag=tag,
            priority=priority,
            leadFor=leadFor,
            fromDate=fromDate,
            toDate=toDate
        )


        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(LEAD_QUERY_CONTROLLER.GetBusinessQueries(user_ins=user_ins,queryParams=queryParams))
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.query_fetch_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })
    
@api_view(['POST'])
async def CreateFunnelQueryView(request):
    try:
        
        # Call Funnel Query Controller to Create Funnel Query
        final_response = await FUNNEL_QUERY_CONTROLLER.CreateFunnelQuery(request=request)

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.funnel_query_create_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })