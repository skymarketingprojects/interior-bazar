import asyncio
from app_ib.Utils.MyMethods import MY_METHODS
from adrf.decorators import api_view
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Controllers.Pages.PagesController import PAGE_CONTROLLER
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated

@api_view(['GET'])
async def GetPagesView(request,page_name):
    try:
        data = MY_METHODS.json_to_object(request.data)
        await MY_METHODS.printStatus(f'get page view data {data}')

        get_page_resp = await PAGE_CONTROLLER.GetPages(page_name=page_name)
        await MY_METHODS.printStatus(f'get page resp {get_page_resp}')

        return ServerResponse(
            response=get_page_resp.response,
            message=get_page_resp.message,
            code=get_page_resp.code,
            data=get_page_resp.data
        )

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.page_fetch_error,
            code=RESPONSE_CODES.error,
            data={
                'error': str(e)
            }
        )
    
@api_view(['GET'])
async def GetQnAView(request):
    try:

        get_qna_resp = await PAGE_CONTROLLER.GetQnA()
        await MY_METHODS.printStatus(f'get qna resp {get_qna_resp}')

        return ServerResponse(
            response=get_qna_resp.response,
            message=get_qna_resp.message,
            code=get_qna_resp.code,
            data=get_qna_resp.data
        )

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.qna_fetch_error,
            code=RESPONSE_CODES.error,
            data={
                'error': str(e)
            }
        )