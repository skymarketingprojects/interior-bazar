import asyncio
from adrf.decorators import api_view
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES,ACCESSLIST

from interior_admin.Controllers.PanelSearch.PanelSearchController import PANEL_SEARCH_CONTROLLER
from interior_admin.Validators.adminValidators import hasAccess

import asyncio
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def SearchQueryView(request:Request,query):
    try:
        await hasAccess(request=request)
        result =  await PANEL_SEARCH_CONTROLLER.GetSearchResults(Query=query)
        return ServerResponse(
            response=result.response,
            message=result.message,
            data= result.data,
            code=result.code
        )

    except Exception as e:
        return ServerResponse(
            response= RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.business_fetch_error,
            code=RESPONSE_CODES.error,
            data={NAMES.ERROR:str(e)}
        )
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def GetBusinessByIdView(request:Request,Id):
    try:
        await hasAccess(request=request)
        result =  await PANEL_SEARCH_CONTROLLER.GetBusinessByID(Id=Id)
        return ServerResponse(
            response=result.response,
            message=result.message,
            data= result.data,
            code=result.code
        )

    except Exception as e:
        return ServerResponse(
            response= RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.business_fetch_error,
            code=RESPONSE_CODES.error,
            data={NAMES.ERROR:str(e)}

        )
