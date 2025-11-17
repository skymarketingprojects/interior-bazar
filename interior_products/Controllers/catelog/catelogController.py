from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse

from .Tasks.catelogTasks import CATELOG_TASKS
from interior_products.Controllers.products.Tasks.productsTasks import PRODUCTS_TASKS
from .Validators.catelogValidators import CATELOG_VALIDATORS
from app_ib.models import Business
from app_ib.Utils.MyMethods import MY_METHODS

from interior_products.models import Catelogue

from django.db.models import Q
from interior_products.models import ProductCategory,ProductSubCategory
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
            
            # await MY_METHODS.printStatus(f"catelog data: {catelogData}")
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.catelog_fetch_success,
                code=RESPONSE_CODES.success,
                data=catelogData
                )

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error during GetCatelogForBusiness: {e}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.catelog_fetch_error,
                code=RESPONSE_CODES.error,
                data={"error":str(e)})
    
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
            # await MY_METHODS.printStatus(f'Error during GetCatelog: {e}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.catelog_fetch_error,
                code=RESPONSE_CODES.error,
                data={

                })
    
    @classmethod
    async def GetAllCatelog(self,page,size,filterType=None,id=None,query=None,state=None):
        try:
            catelogData = []
            related_qs = []
            if filterType and id:
                if filterType == "category":
                    category = ProductCategory.objects.get(id=int(id))
                    related_qs = category.catCatelogues.all()
                elif filterType == "subCategory":
                    subCategory = ProductSubCategory.objects.get(id=int(id))
                    related_qs = subCategory.catSubCatelogues.all()
            else:
                related_qs = Catelogue.objects.all()
            if related_qs.count() == 0:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.catelog_fetch_error,
                    code=RESPONSE_CODES.error,
                    data={'error':'No catelog found'}
                )
            paginated = await MY_METHODS.paginate_queryset(related_qs, page, size)
            catelogData = []

            for c in paginated["results"]:
                data = await CATELOG_TASKS.getCatelog(c)
                if data:
                    catelogData.append(data)

            paginated['pagination']['data'] = catelogData
            

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.catelog_fetch_success,
                code=RESPONSE_CODES.success,
                data=paginated['pagination']
                )

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error during GetCatelog: {e}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.catelog_fetch_error,
                code=RESPONSE_CODES.error,
                data={'error':str(e)})

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
            # await MY_METHODS.printStatus(f'Error during CreateCatelog: {e}')
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
            # await MY_METHODS.printStatus(f'Error during UpdateCatelog: {e}')
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
            # await MY_METHODS.printStatus(f'Error during DeleteCatelog: {e}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.catelog_delete_error,
                code=RESPONSE_CODES.error,
                data={'error':str(e)}
            )
        
    @classmethod
    async def GetRelatedCatelogs(cls, catelogId: int, page: int = 1, size: int = 10):
        try:
            catelog = Catelogue.objects.get(id=catelogId)
            related_qs = Catelogue.objects.filter(
                            Q(category=catelog.category)
                            | Q(catelogueType=catelog.catelogueType)
                            | Q(title__icontains=catelog.title.split(" ")[0])
                        ).exclude(id=catelog.id)
            paginated = await MY_METHODS.paginate_queryset(related_qs, page, size)
            catelogData = []

            for c in paginated["results"]:
                data = await CATELOG_TASKS.getCatelog(c)
                if data:
                    catelogData.append(data)

            paginated['pagination']['data'] = catelogData
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message="Related catelogues fetched successfully",
                code=RESPONSE_CODES.success,
                data=paginated["pagination"]
            )
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Error fetching related catelogues",
                code=RESPONSE_CODES.error,
                data={"error": str(e)}
            )
        
    @classmethod
    async def GetCatelougeTab(cls):
        try:
            categorys = ProductCategory.objects.all()
            tabData = []


            for category in categorys:
                if category.catCatelogues.all().count():
                    categoryData = await PRODUCTS_TASKS.getCategoriesDataTask(category)
                    if categoryData:
                        categoryData['type']='category'
                        tabData.append(categoryData)


            subCategorys = ProductSubCategory.objects.all()
            for subCategory in subCategorys:
                if subCategory.catSubCatelogues.all().count():
                    subCategoryData = await PRODUCTS_TASKS.getCategoriesDataTask(subCategory)
                    if subCategoryData:
                        subCategoryData['type']='subCategory'
                        tabData.append(subCategoryData)

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.catelog_table_success,
                code=RESPONSE_CODES.success,
                data=tabData
                )
        except Exception as e:
            await MY_METHODS.printStatus(f'Error during GetCatelougeTab: {str(e)}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.catelog_table_error,
                code=RESPONSE_CODES.error,
                data={'error':str(e)}
                )
                    


