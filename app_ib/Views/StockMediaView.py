from adrf.decorators import api_view
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES

from app_ib.Controllers.StockMediaController.StockMediaController import StockMediaController

@api_view(['GET'])
async def GetStockMedia(request,page,section):
    try:
        final_response= await StockMediaController.getStockMedia(pagename=page,sectionname=section)
        # print(f"final_response {final_response}")
        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data
            )
    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.default_error,
            code=RESPONSE_CODES.error,
            data={
                'error': str(e)
            })
