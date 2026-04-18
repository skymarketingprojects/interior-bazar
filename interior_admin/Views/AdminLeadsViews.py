
from adrf.decorators import api_view

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.Names import NAMES,ACCESSLIST
from app_ib.decorators.ViewDecorator import exceptionHandler
from app_ib.Utils.MyMethods import MY_METHODS

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
        await hasAccess(request=request)
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
            await hasAccess(request=request)
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
        async def get(self,request:Request):
            user = request.user
            await hasAccess(request=request)
            
            # Extract all query params to allow full filtration
            params = AdminLeadQueryFilters(**request.query_params.dict())
            
            # Call Auth Controller to Fetch Queries
            final_response = await  ADMIN_LEADS_CONTROLLER_V2.GetQueries(queryParams=params)
            await MY_METHODS.printStatus(f'GetAdminQueryView final response:-{final_response}')

            return final_response
        
        @exceptionHandler(
            errorMessage=RESPONSE_MESSAGES.query_fetch_error,
            responseFunc=ServerResponse
        )
        async def post(self,request:Request):
            await hasAccess(request=request)
            data = AdminLeadsCreateSchema(**request.data)
            # Call Auth Controller to Create User
            final_response = await  ADMIN_LEADS_CONTROLLER_V2.createQuery(data=data)

            return final_response
    
        @exceptionHandler(
            errorMessage=RESPONSE_MESSAGES.query_update_error,
            responseFunc=ServerResponse
        )
        async def put(self,request:Request,leadId):
            await hasAccess(request=request)
            data = AdminLeadsUpdateSchema(**request.data)
            # Call Auth Controller to Create User
            final_response = await  ADMIN_LEADS_CONTROLLER_V2.updateQuery(data=data,leadId=leadId)
            await MY_METHODS.printStatus(f'UpdateAdminQueryView final response:-{final_response}')
            return final_response
        
        @exceptionHandler(
            errorMessage=RESPONSE_MESSAGES.query_remove_error,
            responseFunc=ServerResponse
        )
        async def delete(self,request:Request,leadId):
            await hasAccess(request=request)
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
            await hasAccess(request=request)
            data = request.data

            businessId = data.get(NAMES.BUSINESS_ID,None)
            leadId = data.get(NAMES.LEAD_ID,None)
            # await MY_METHODS.printStatus(status=f"businessId {businessId}--lead {leadId}")
            assignResponse = await ADMIN_LEADS_CONTROLLER_V2.AssignLeadQuery(user_ins=user,businessId=businessId,leadId=leadId)
            return assignResponse
        
