from app_ib.models import StockMedia, Page, Section
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from asgiref.sync import sync_to_async
from app_ib.Utils.Names import NAMES

def getStockData(stockMedia:StockMedia):
    try:
        stockData = {
            NAMES.ID: stockMedia.id,
            NAMES.INDEX: stockMedia.index
        }
        if stockMedia.image:
            stockData[NAMES.IMAGE] = stockMedia.image
        if stockMedia.video:
            stockData[NAMES.VIDEO] = stockMedia.video
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
            data={NAMES.ERROR: str(e)}
        )