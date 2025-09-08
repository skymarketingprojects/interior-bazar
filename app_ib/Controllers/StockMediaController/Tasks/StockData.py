from app_ib.models import StockMedia, Page, Section
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from asgiref.sync import sync_to_async


def getStockData(stockMedia):
    try:
        stockData = {
            "id": stockMedia.id,
            "index": stockMedia.index
        }
        if stockMedia.image:
            stockData["image"] = stockMedia.image
        if stockMedia.video:
            stockData["video"] = stockMedia.video
        return LocalResponse(
            response=RESPONSE_MESSAGES.success,
            code=RESPONSE_CODES.success,
            message=RESPONSE_MESSAGES.stock_media_fetched,
            data=stockData
        )
    except Exception as e:
        return LocalResponse(
            response=RESPONSE_MESSAGES.success,
            code=RESPONSE_CODES.error,
            message=RESPONSE_MESSAGES.stock_media_not_found,
            data={"error": str(e)}
        )