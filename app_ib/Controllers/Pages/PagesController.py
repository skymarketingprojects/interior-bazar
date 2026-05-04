from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.models import Pages,QNA
from django.core.cache import cache

class PAGE_CONTROLLER:

    @classmethod
    async def GetPages(self, page_name):
        cache_key = f"static_page_{page_name}"
        cached_data = await cache.aget(cache_key)
        if cached_data:
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.page_fetch_success,
                code=RESPONSE_CODES.success,
                data=cached_data)

        try:
            page_ins = await sync_to_async(Pages.objects.get)(pageName=page_name)
            page_data = {
                NAMES.ID: page_ins.id,
                NAMES.PAGE_NAME: page_ins.pageName,
                NAMES.PAGE_TITLE: page_ins.title,
                NAMES.PAGE_CONTENT: page_ins.content.html,
            }
            # Cache for 24 hours
            await cache.aset(cache_key, page_data, 86400)
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.page_fetch_success,
                code=RESPONSE_CODES.success,
                data=page_data)

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.page_fetch_error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR:str(e)}
            )
    @classmethod
    async def GetQnA(self):
        cache_key = "static_qna_list"
        cached_data = await cache.aget(cache_key)
        if cached_data:
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.qna_fetch_success,
                code=RESPONSE_CODES.success,
                data=cached_data)

        try:
            qna_list = []
            qna_qs = await sync_to_async(QNA.objects.all)()
            qna_ins = await sync_to_async(list)(qna_qs)
            for qna in qna_ins:
                qna_data = {
                    NAMES.ID: qna.id,
                    NAMES.QUESTION: qna.question,
                    NAMES.ANSWER: qna.answer,
                }
                qna_list.append(qna_data)
            
            # Cache for 24 hours
            await cache.aset(cache_key, qna_list, 86400)
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.qna_fetch_success,
                code=RESPONSE_CODES.success,
                data=qna_list)

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.qna_fetch_error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR:str(e)}
            )