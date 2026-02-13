
from adrf.decorators import api_view

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.Names import NAMES,ACCESSLIST
from app_ib.decorators.ViewDecorator import exceptionHandler

import asyncio
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from interior_admin.Controllers.AdminLeads.AdminLeadsController import ADMIN_LEADS_CONTROLLER, ADMIN_LEADS_CONTROLLER_V2
from interior_admin.Controllers.AdminLeads.Validators.AdminLeadsValidators import AdminLeadQueryFilters,AdminLeadsCreateSchema,AdminLeadsUpdateSchema
from interior_admin.Validators.adminValidators import hasAccess

from adrf.views import APIView 

from rest_framework.request import Request


class AdminLeadsViewsV1:
    @api_view(['GET'])
    @permission_classes([IsAuthenticated])
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.query_fetch_error,
        responseFunc=ServerResponse
    )
    async def GetAdminQueryView(request:Request,pageNo,pageSize):
        hasAccess(user=request.user, accessName=ACCESSLIST.ACCESS_QUERY_VIEW)
        user = request.user
        # Call Auth Controller to Create User
        final_response = await  ADMIN_LEADS_CONTROLLER.GetQueries(user_ins=user,pageNo=pageNo,size=pageSize)

        return final_response

    @api_view(['POST'])
    @permission_classes([IsAuthenticated])
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.query_fetch_error,
        responseFunc=ServerResponse
    )
    async def AssignQueryView(request:Request):
            hasAccess(user=request.user, accessName=ACCESSLIST.ACCESS_QUERY_VIEW)
            user = request.user
            data = request.data
            businessId = data.get(NAMES.BUSINESS_ID,None)
            leadId = data.get(NAMES.LEAD_ID,None)
            # await MY_METHODS.printStatus(status=f"businessId {businessId}--lead {leadId}")
            assignResponse = await ADMIN_LEADS_CONTROLLER.AssignLeadQuery(user_ins=user,businessId=businessId,leadId=leadId)
            return assignResponse


class AdminLeadsViewsV2:


    class QueryViews(APIView):
        permission_classes = [IsAuthenticated]

        @exceptionHandler(
            errorMessage=RESPONSE_MESSAGES.query_fetch_error,
            responseFunc=ServerResponse
        )
        async def get(request:Request):
            user = request.user
            hasAccess(user=user, accessName=ACCESSLIST.ACCESS_QUERY_VIEW)
            params = AdminLeadQueryFilters(**request.query_params)
            # Call Auth Controller to Create User
            final_response = await  ADMIN_LEADS_CONTROLLER_V2.GetQueries(user_ins=user,queryParams=params)

            return final_response
        
        @exceptionHandler(
            errorMessage=RESPONSE_MESSAGES.query_fetch_error,
            responseFunc=ServerResponse
        )
        async def post(request:Request):
            hasAccess(user=request.user, accessName=ACCESSLIST.ACCESS_QUERY_VIEW)
            data = AdminLeadsCreateSchema(**request.data)
            # Call Auth Controller to Create User
            final_response = await  ADMIN_LEADS_CONTROLLER_V2.createQuery(data=data)

            return final_response
    
        @exceptionHandler(
            errorMessage=RESPONSE_MESSAGES.query_update_error,
            responseFunc=ServerResponse
        )
        async def put(request:Request,leadId):
            hasAccess(user=request.user, accessName=ACCESSLIST.ACCESS_QUERY_VIEW)
            data = AdminLeadsUpdateSchema(**request.data)
            # Call Auth Controller to Create User
            final_response = await  ADMIN_LEADS_CONTROLLER_V2.updateQuery(data=data,leadId=leadId)

            return final_response
        
        @exceptionHandler(
            errorMessage=RESPONSE_MESSAGES.query_remove_error,
            responseFunc=ServerResponse
        )
        async def delete(request:Request,leadId):
            hasAccess(user=request.user, accessName=ACCESSLIST.ACCESS_QUERY_VIEW)
            final_response = await  ADMIN_LEADS_CONTROLLER_V2.deleteQuery(leadId=leadId)

            return final_response

    @api_view(['POST'])
    @permission_classes([IsAuthenticated])
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.query_fetch_error,
        responseFunc=ServerResponse
    )
    async def AssignQueryView(request:Request):
            user = request.user
            hasAccess(user=request.user, accessName=ACCESSLIST.ACCESS_QUERY_VIEW)
            data = request.data

            businessId = data.get(NAMES.BUSINESS_ID,None)
            leadId = data.get(NAMES.LEAD_ID,None)
            # await MY_METHODS.printStatus(status=f"businessId {businessId}--lead {leadId}")
            assignResponse = await ADMIN_LEADS_CONTROLLER_V2.AssignLeadQuery(user_ins=user,businessId=businessId,leadId=leadId)
            return assignResponse
        
