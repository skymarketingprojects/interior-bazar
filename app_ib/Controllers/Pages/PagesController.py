from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.models import Pages,QNA
# from app_ib.Controllers.Pages.Tasks.PagesTasks import PAGE_TASKS

class PAGE_CONTROLLER:

    @classmethod
    async def GetPages(self,page_name):
        try:
            await MY_METHODS.printStatus(f'page name: {page_name}')
            page_ins=await sync_to_async(Pages.objects.get)(page_name=page_name)
            await MY_METHODS.printStatus(f'page ins {page_ins}')
            page_data={
                'id':page_ins.id,
                'page_name':page_ins.page_name,
                'page_title':page_ins.title,
                'page_content':page_ins.content.html,
            }
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.page_fetch_success,
                code=RESPONSE_CODES.success,
                data= page_data)

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.page_fetch_error,
                code=RESPONSE_CODES.error,
                data={}
            )
    @classmethod
    async def GetQnA(self):
        try:
            qna_list=[]
            qna_ins=await sync_to_async(QNA.objects.all)()
            for qna in qna_ins:
                qna_data={
                    'id':qna.id,
                    'question':qna.question,
                    'answer':qna.answer,
                }
                qna_list.append(qna_data)
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
                data={}
            )