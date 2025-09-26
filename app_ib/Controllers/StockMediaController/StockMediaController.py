import asyncio
from asgiref.sync import sync_to_async
from django.db import transaction

from app_ib.models import StockMedia, Page, Section
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.MyMethods import MY_METHODS

from .Tasks.StockData import getStockData  # Should be async or wrapped

class StockMediaController:
    @staticmethod
    async def getStockMedia(pagename, sectionname):
        try:
            # Fetch page and section
            page = await sync_to_async(Page.objects.get)(name__iexact=pagename)
            section = await sync_to_async(Section.objects.get)(name__iexact=sectionname)

            # Query related StockMedia
            stock_media_qs = await sync_to_async(list)(
                StockMedia.objects.filter(page=page, section=section).order_by("index")
            )

            if not stock_media_qs:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    code=RESPONSE_CODES.error,
                    message=RESPONSE_MESSAGES.stock_media_not_found,
                    data={},
                    local=True
                )

            # Get media data
            data = []
            for media in stock_media_qs:
                # Wrap getStockData if it's not async
                mediadataresp = await sync_to_async(getStockData)(media)
                # #await MY_METHODS.printStatus(f"mediadataresp {mediadataresp}")
                if mediadataresp.response == RESPONSE_MESSAGES.success:
                    data.append(mediadataresp.data)

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                code=RESPONSE_CODES.success,
                message=RESPONSE_MESSAGES.stock_media_fetched,
                data=data
            )

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                code=RESPONSE_CODES.error,
                message=RESPONSE_MESSAGES.stock_media_not_found,
                data={"error": str(e)}
            )

    @staticmethod
    async def saveStockMedia(data):
        try:
            # Start atomic transaction safely in async
            @sync_to_async
            @transaction.atomic
            def save_media_sync():
                stockMedia = StockMedia()
                pageName = data.get("page")
                sectionName = data.get("section")
                
                page, _ = Page.objects.get_or_create(name=pageName.lower())
                section, _ = Section.objects.get_or_create(name=sectionName.lower())

                stockMedia.page = page
                stockMedia.section = section

                if "image" in data:
                    stockMedia.image = data["image"]
                elif "video" in data:
                    stockMedia.video = data["video"]

                if "index" in data:
                    stockMedia.index = data["index"]

                stockMedia.save()
                return stockMedia

            # Save stock media
            saved_media = await save_media_sync()

            # Get media data
            mediadataresp = await getStockData(saved_media)

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                code=RESPONSE_CODES.success,
                message=RESPONSE_MESSAGES.stock_media_fetched,
                data=mediadataresp.data
            )

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                code=RESPONSE_CODES.error,
                message=RESPONSE_MESSAGES.stock_media_not_saved,
                data={"error": str(e)}
            )
