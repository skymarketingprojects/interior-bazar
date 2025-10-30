from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse

from .Tasks.catelogTasks import CATELOG_TASKS
from .Validators.catelogValidators import CATELOG_VALIDATORS
from app_ib.models import Business
from app_ib.Utils.MyMethods import MY_METHODS

from interior_products.models import Catelogue


class CATELOG_CONTROLLER:
    
    @classmethod
    async def GetCatelogForBusiness(self, business):
        try:
            catelogs = Catelogue.objects.filter(business=business)
            catelogData= []
            for catelog in catelogs:
                data = await CATELOG_TASKS.getCatelog(catelog)
                if data:
                    catelogData.append(data)
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.catelog_fetch_success,
                code=RESPONSE_CODES.success,
                data=catelogData
                )

        except Exception as e:
            #await MY_METHODS.printStatus(f'Error during GetCatelogForBusiness: {e}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.catelog_fetch_error,
                code=RESPONSE_CODES.error,
                data={

                })
    
    @classmethod
    async def GetCatelog(self, catelogId):
        try:
            catelog = Catelogue.objects.get(pk=catelogId)
            catelogData = await CATELOG_TASKS.getCatelog(catelog)
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.catelog_fetch_success,
                code=RESPONSE_CODES.success,
                data=catelogData
                )

        except Exception as e:
            #await MY_METHODS.printStatus(f'Error during GetCatelog: {e}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.catelog_fetch_error,
                code=RESPONSE_CODES.error,
                data={

                })
    @classmethod
    async def CreateCatelog(self, business, data):
        try:
            catelog = await CATELOG_TASKS.createCatelog(business, data)
            if not catelog:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.catelog_create_error,
                    code=RESPONSE_CODES.error,
                    data={}
                    )
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.catelog_create_success,
                code=RESPONSE_CODES.success,
                data=catelog
                )

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.catelog_create_error,
                code=RESPONSE_CODES.error,
                data={}
                )

    @classmethod
    async def UpdateCatelog(self,business, data,catelogId):
        try:
            catelogExist = Catelogue.objects.filter(pk=catelogId,business=business).exists()
            if not catelogExist:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.catelog_update_error,
                    code=RESPONSE_CODES.error,
                    data={}
                    )
            catelog = Catelogue.objects.get(pk=catelogId,business=business)
            catelog = await CATELOG_TASKS.updateCatelog(catelog, data)
            if not catelog:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.catelog_update_error,
                    code=RESPONSE_CODES.error,
                    data={}
                    )
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.catelog_update_success,
                code=RESPONSE_CODES.success,
                data=catelog
                )

        except Exception as e:
            #await MY_METHODS.printStatus(f'Error during UpdateCatelog: {e}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.catelog_update_error,
                code=RESPONSE_CODES.error,
                data={}
                )
    @classmethod
    async def DeleteCatelog(self,business,catelogId):
        try:
            catelogExist = Catelogue.objects.filter(pk=catelogId,business=business).exists()
            if not catelogExist:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.catelog_delete_error,
                    code=RESPONSE_CODES.error,
                    data={}
                    )
            catelog = Catelogue.objects.get(pk=catelogId,business=business)
            catelog = await CATELOG_TASKS.deleteCatelog(catelog)
            if not catelog:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.catelog_delete_error,
                    code=RESPONSE_CODES.error,
                    data={}
                    )
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.catelog_delete_success,
                code=RESPONSE_CODES.success,
                data=catelog
                )

        except Exception as e:
            #await MY_METHODS.printStatus(f'Error during DeleteCatelog: {e}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.catelog_delete_error,
                code=RESPONSE_CODES.error,
                data={'error':str(e)}
            )