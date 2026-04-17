from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from .Tasks.catelogTasks import CATELOG_TASKS
from interior_products.Controllers.products.Tasks.productsTasks import PRODUCTS_TASKS
from app_ib.models import Business
from app_ib.Utils.MyMethods import MY_METHODS
from interior_products.models import Catelogue, CatelogueImage, ProductCategory, ProductSubCategory
from django.db.models import Q, Prefetch, Count
import asyncio

class CATELOG_CONTROLLER:
    
    @classmethod
    async def GetCatelogForBusiness(cls, business):
        try:
            queryset = Catelogue.objects.filter(business=business).select_related(
                'catelogueType', 'business', 'business__user', 'business__user__user_profile'
            ).prefetch_related('catelogueImages', 'catalogCategory', 'subCategory')
            
            catelogs = await sync_to_async(list)(queryset)
            data = await CATELOG_TASKS.BulkSerializeCatelogs(catelogs)
            
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.catelog_fetch_success,
                code=RESPONSE_CODES.success,
                data=data)
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.catelog_fetch_error,
                code=RESPONSE_CODES.error,
                data={"error": str(e)})
    
    @classmethod
    async def GetAllCatelog(cls, page, size, filterType=None, id=None, query=None, state=None):
        try:
            filterQuery = Q()
            if state:
                filterQuery &= Q(business__business_location__locationState__value__iexact=state)
            
            if filterType and id:
                if filterType == "category":
                    filterQuery &= Q(catalogCategory__id=int(id))
                elif filterType == "subCategory":
                    filterQuery &= Q(subCategory__id=int(id))

            if query:
                q_obj = Q(title__icontains=query)
                q_obj |= Q(catalogCategory__lable__icontains=query)
                q_obj |= Q(subCategory__lable__icontains=query)
                filterQuery &= q_obj

            related_qs = Catelogue.objects.filter(filterQuery).select_related(
                'catelogueType', 'business', 'business__user', 'business__user__user_profile'
            ).prefetch_related('catelogueImages', 'catalogCategory', 'subCategory').order_by('index')

            paginated = await MY_METHODS.paginate_queryset(related_qs, page, size)
            catelog_list = paginated["results"] # Already list from paginate_queryset
            
            data = await CATELOG_TASKS.BulkSerializeCatelogs(catelog_list)
            paginated['pagination']['data'] = data
            
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.catelog_fetch_success,
                code=RESPONSE_CODES.success,
                data=paginated['pagination'])
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.catelog_fetch_error,
                code=RESPONSE_CODES.error,
                data={'error': str(e)})

    @classmethod
    async def GetRelatedCatelogs(cls, catelogId: int, page: int = 1, size: int = 10):
        try:
            base_cat = await sync_to_async(Catelogue.objects.get)(id=catelogId)
            related_qs = Catelogue.objects.filter(
                Q(category=base_cat.category) | Q(catelogueType=base_cat.catelogueType) |
                Q(title__icontains=base_cat.title.split(" ")[0])
            ).select_related(
                'catelogueType', 'business', 'business__user', 'business__user__user_profile'
            ).prefetch_related('catelogueImages', 'catalogCategory', 'subCategory').exclude(id=base_cat.id)

            paginated = await MY_METHODS.paginate_queryset(related_qs, page, size)
            data = await CATELOG_TASKS.BulkSerializeCatelogs(paginated["results"])
            paginated['pagination']['data'] = data

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message="Related catelogues fetched successfully",
                code=RESPONSE_CODES.success,
                data=paginated["pagination"])
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Error fetching related catelogues",
                code=RESPONSE_CODES.error,
                data={"error": str(e)})

    @classmethod
    async def GetCatelougeTab(cls):
        try:
            # Optimized tab fetching with annotated counts and pre-fetching
            cat_qs = ProductCategory.objects.annotate(num_entries=Count('catCatelogues'))
            sub_qs = ProductSubCategory.objects.annotate(num_entries=Count('catSubCatelogues'))
            
            cats, subs = await asyncio.gather(sync_to_async(list)(cat_qs), sync_to_async(list)(sub_qs))
            
            tabData = []
            for c in cats:
                data = PRODUCTS_TASKS.getCategoriesDataSync(c)
                data['type'] = 'category'
                tabData.append(data)
                
            for s in subs:
                data = PRODUCTS_TASKS.getCategoriesDataSync(s)
                data['type'] = 'subCategory'
                tabData.append(data)

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.catelog_table_success,
                code=RESPONSE_CODES.success,
                data=tabData)
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.catelog_table_error,
                code=RESPONSE_CODES.error,
                data={'error': str(e)})

    @classmethod
    async def GetCatelog(cls, catelogId):
        try:
            queryset = Catelogue.objects.filter(pk=catelogId).select_related(
                'catelogueType', 'business', 'business__user', 'business__user__user_profile'
            ).prefetch_related('catelogueImages', 'catalogCategory', 'subCategory')
            
            objs = await sync_to_async(list)(queryset)
            data = await CATELOG_TASKS.BulkSerializeCatelogs(objs)
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.catelog_fetch_success,
                code=RESPONSE_CODES.success,
                data=data[0] if data else None)
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.catelog_fetch_error,
                code=RESPONSE_CODES.error,
                data={"error": str(e)})

    @classmethod
    async def CreateCatelog(cls, business, data):
        data = await CATELOG_TASKS.createCatelog(business, data)
        if not data: return LocalResponse(response=RESPONSE_MESSAGES.error, message=RESPONSE_MESSAGES.catelog_create_error, code=RESPONSE_CODES.error, data={})
        return LocalResponse(response=RESPONSE_MESSAGES.success, message=RESPONSE_MESSAGES.catelog_create_success, code=RESPONSE_CODES.success, data=data)

    @classmethod
    async def UpdateCatelog(cls, business, data, catelogId):
        cat = await sync_to_async(Catelogue.objects.filter(pk=catelogId, business=business).first)()
        if not cat: return LocalResponse(response=RESPONSE_MESSAGES.error, message=RESPONSE_MESSAGES.catelog_update_error, code=RESPONSE_CODES.error, data={})
        data = await CATELOG_TASKS.updateCatelog(cat, data)
        if not data: return LocalResponse(response=RESPONSE_MESSAGES.error, message=RESPONSE_MESSAGES.catelog_update_error, code=RESPONSE_CODES.error, data={})
        return LocalResponse(response=RESPONSE_MESSAGES.success, message=RESPONSE_MESSAGES.catelog_update_success, code=RESPONSE_CODES.success, data=data)

    @classmethod
    async def DeleteCatelog(cls, business, catelogId):
        cat = await sync_to_async(Catelogue.objects.filter(pk=catelogId, business=business).first)()
        if not cat: return LocalResponse(response=RESPONSE_MESSAGES.error, message=RESPONSE_MESSAGES.catelog_delete_error, code=RESPONSE_CODES.error, data={})
        res = await CATELOG_TASKS.deleteCatelog(cat)
        if not res: return LocalResponse(response=RESPONSE_MESSAGES.error, message=RESPONSE_MESSAGES.catelog_delete_error, code=RESPONSE_CODES.error, data={})
        return LocalResponse(response=RESPONSE_MESSAGES.success, message=RESPONSE_MESSAGES.catelog_delete_success, code=RESPONSE_CODES.success, data=res)
