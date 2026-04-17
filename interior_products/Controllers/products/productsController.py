from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.MyMethods import MY_METHODS

from .Tasks.productsTasks import PRODUCTS_TASKS
from .Validators.productsValidators import PRODUCTS_VALIDATORS
from app_ib.models import Business
from interior_products.models import Product, ProductCategory, ProductSubCategory
from django.db.models import Q, Count
from app_ib.Utils.Names import NAMES

class PRODUCTS_CONTROLLER:

    @classmethod
    async def getProduct(cls, productId: int) -> LocalResponse:
        try:
            queryset = Product.objects.filter(id=productId).select_related(
                'catelogue', 'business', 'business__user', 'business__user__user_profile'
            ).prefetch_related(
                'productImages', 'category', 'subCategory', 'productSpecifications'
            )
            product = await sync_to_async(queryset.first)()
            if not product:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.product_fetch_error,
                    code=RESPONSE_CODES.error,
                    data={'error': RESPONSE_MESSAGES.product_fetch_error}
                )
            
            productData = await PRODUCTS_TASKS.getProduct(product)
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.product_fetch_success,
                code=RESPONSE_CODES.success,
                data=productData
            )
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.product_fetch_error,
                code=RESPONSE_CODES.error,
                data={'error': str(e)}
            )
    
    @classmethod
    async def getAllProduct(cls, page, size, filterType=None, id=None, state=None, query=None):
        try:
            filterQuery = Q()
            if state:
                filterQuery &= Q(business__business_location__locationState__value__iexact=state)
            
            if filterType and id:
                if filterType == "category":
                    filterQuery &= Q(category__id=int(id))
                elif filterType == "subCategory":
                    filterQuery &= Q(subCategory__id=int(id))

            if query:
                q_obj = Q(title__icontains=query)
                q_obj |= Q(category__lable__icontains=query)
                q_obj |= Q(subCategory__lable__icontains=query)
                filterQuery &= q_obj

            queryset = Product.objects.filter(filterQuery).select_related(
                'catelogue', 'business', 'business__user', 'business__user__user_profile'
            ).prefetch_related(
                'productImages', 'category', 'subCategory', 'productSpecifications'
            ).order_by('index')

            paginated = await MY_METHODS.paginate_queryset(queryset, page, size)
            
            # Optimized bulk serialization
            productData = await PRODUCTS_TASKS.BulkSerializeProducts(paginated["results"])
            paginated['pagination']['data'] = productData
                
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.product_fetch_success,
                code=RESPONSE_CODES.success,
                data=paginated['pagination']
            )
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.product_fetch_error,
                code=RESPONSE_CODES.error,
                data={'error': str(e)}
            )
    
    @classmethod
    async def getProductsForBusiness(cls, business: Business) -> LocalResponse:
        try:
            queryset = business.products.select_related(
                'catelogue', 'business', 'business__user', 'business__user__user_profile'
            ).prefetch_related(
                'productImages', 'category', 'subCategory', 'productSpecifications'
            ).order_by('index')
            
            products_list = await sync_to_async(list)(queryset)
            productsData = await PRODUCTS_TASKS.BulkSerializeProducts(products_list)
            
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.products_fetch_success,
                code=RESPONSE_CODES.success,
                data=productsData
            )
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.products_fetch_error,
                code=RESPONSE_CODES.error,
                data={'error': str(e)}
            )
        
    @classmethod
    async def createProduct(cls, business: Business, data: dict) -> LocalResponse:
        try:
            product = await PRODUCTS_TASKS.createProduct(business, data)
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.product_create_success,
                code=RESPONSE_CODES.success,
                data=product
            )
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.product_create_error,
                code=RESPONSE_CODES.error,
                data={'error': str(e)}
            )
    
    @classmethod
    async def updateProduct(cls, business: Business, productId: int, data: dict) -> LocalResponse:
        try:
            product = await sync_to_async(Product.objects.get)(id=productId, business=business)
            product = await PRODUCTS_TASKS.updateProduct(product, data)
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.product_update_success,
                code=RESPONSE_CODES.success,
                data=product
            )
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.product_update_error,
                code=RESPONSE_CODES.error,
                data={'error': str(e)}
            )
    
    @classmethod
    async def deleteProduct(cls, business: Business, productId: int) -> LocalResponse:
        try:
            product = await sync_to_async(Product.objects.get)(id=productId, business=business)
            success = await PRODUCTS_TASKS.deleteProduct(product)
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.product_delete_success,
                code=RESPONSE_CODES.success,
                data=success
            )
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.product_delete_error,
                code=RESPONSE_CODES.error,
                data={'error': str(e)}
            )
        
    @classmethod
    async def GetRelatedProducts(cls, productId: int, page: int = 1, size: int = 10):
        try:
            product = await sync_to_async(Product.objects.get)(id=productId)
            related_qs = Product.objects.filter(
                                Q(title__icontains=product.title.split(" ")[0])
                                | Q(business=product.business)
                            ).exclude(id=product.id).select_related(
                                'catelogue', 'business', 'business__user', 'business__user__user_profile'
                            ).prefetch_related(
                                'productImages', 'category', 'subCategory', 'productSpecifications'
                            ).order_by(NAMES.INDEX)

            paginated = await MY_METHODS.paginate_queryset(related_qs, page, size)
            productData = await PRODUCTS_TASKS.BulkSerializeProducts(paginated["results"])
            paginated['pagination']['data'] = productData

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message="Related products fetched successfully",
                code=RESPONSE_CODES.success,
                data=paginated["pagination"]
            )
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Error fetching related products",
                code=RESPONSE_CODES.error,
                data={"error": str(e)}
            )
        
    @classmethod
    async def GetProductCategories(cls):
        try:
            categories = await PRODUCTS_TASKS.getProductCategoriesTask()
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message="Categories fetched successfully",
                code=RESPONSE_CODES.success,
                data=categories
            )
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Categories fetched Failed",
                code=RESPONSE_CODES.error,
                data={"error": str(e)}
            )
    
    @classmethod
    async def GetProductSubCategories(cls):
        try:
            categories = await PRODUCTS_TASKS.getProductSubCategoriesTask()
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message="Sub Categories fetched successfully",
                code=RESPONSE_CODES.success,
                data=categories
            )
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Sub Categories fetched Failed",
                code=RESPONSE_CODES.error,
                data={"error": str(e)}
            )

    @classmethod
    async def GetProductTab(cls):
        try:
            # Use annotation to count related products efficiently
            categories = ProductCategory.objects.annotate(prod_count=Count('catProducts'))
            sub_categories = ProductSubCategory.objects.annotate(prod_count=Count('subcatProducts'))
            
            tabData = []
            # Fetch all in bulk
            cat_list = await sync_to_async(list)(categories)
            for category in cat_list:
                categoryData = PRODUCTS_TASKS.getCategoriesDataSync(category)
                categoryData['type'] = 'category'
                tabData.append(categoryData)
                
            sub_list = await sync_to_async(list)(sub_categories)
            for subCategory in sub_list:
                subCategoryData = PRODUCTS_TASKS.getCategoriesDataSync(subCategory)
                subCategoryData['type'] = 'subCategory'
                tabData.append(subCategoryData)
                
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.product_tab_success,
                code=RESPONSE_CODES.success,
                data=tabData
            )
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.product_tab_error,
                code=RESPONSE_CODES.error,
                data={'error': str(e)}
            )