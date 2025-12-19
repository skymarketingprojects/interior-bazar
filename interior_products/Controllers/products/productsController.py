from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.MyMethods import MY_METHODS

from .Tasks.productsTasks import PRODUCTS_TASKS
from .Validators.productsValidators import PRODUCTS_VALIDATORS
from app_ib.models import Business
from interior_products.models import Product,ProductCategory,ProductSubCategory
from django.db.models import Q
from app_ib.Utils.Names import NAMES

class PRODUCTS_CONTROLLER:

    @classmethod
    async def getProduct(self,productId:int)->LocalResponse:
        try:
            product = await sync_to_async(Product.objects.get)(id=productId)
            if not product:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.product_fetch_error,
                    code=RESPONSE_CODES.error,
                    data={'error':RESPONSE_MESSAGES.product_fetch_error}
                )
            productData = await PRODUCTS_TASKS.getProduct(product)
            if not productData:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.product_fetch_error,
                    code=RESPONSE_CODES.error,
                    data={'error':RESPONSE_MESSAGES.product_fetch_error}
                )
            
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.product_fetch_success,
                code=RESPONSE_CODES.success,
                data=productData
            )
        except Exception as e:
            # await MY_METHODS.printStatus(f"Error in getProduct: {str(e)}")
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.product_fetch_error,
                code=RESPONSE_CODES.error,
                data={'error':str(e)}
            )
    
    @classmethod
    async def getAllProduct(self,page,size,filterType=None,id=None,state=None,query=None):
        try:
            productData = []
            related_qs = []
            filterQuery=Q()
            
            if state:
                filterQuery |= Q(business__business_location__locationState__value__iexact=state)
            if query:
                filterQuery |= Q(value__icontains=query)
                filterQuery |= Q(lable__icontains=query)
            
            if filterType and id:
                if filterType == "category":
                    filterQuery |= Q(catProducts__id=int(id))
                elif filterType == "subCategory":
                    filterQuery |= Q(subcatProducts__id=int(id))

            if filterQuery:
                related_qs = Product.objects.filter(filterQuery).order_by('index')
            else:
                related_qs = Product.objects.all().order_by('index')
            # await MY_METHODS.printStatus(f"related_qs: {related_qs}")

            if not related_qs.count():
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.product_fetch_error,
                    code=RESPONSE_CODES.error,
                    data={'error':RESPONSE_MESSAGES.product_fetch_error}
                )
            paginated = await MY_METHODS.paginate_queryset(related_qs, page, size)
            productData = []

            for c in paginated["results"]:
                data = await PRODUCTS_TASKS.getProduct(c)
                if data:
                    productData.append(data)

            paginated['pagination']['data'] = productData
                
            if not productData:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.product_fetch_error,
                    code=RESPONSE_CODES.error,
                    data={'error':RESPONSE_MESSAGES.product_fetch_error}
                )
            
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.product_fetch_success,
                code=RESPONSE_CODES.success,
                data=paginated['pagination']
            )
        except Exception as e:
            # await MY_METHODS.printStatus(f"Error in getProduct: {str(e)}")
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.product_fetch_error,
                code=RESPONSE_CODES.error,
                data={'error':str(e)}
            )
    
    @classmethod
    async def getProductsForBusiness(self,business:Business)->LocalResponse:
        try:
            products = await sync_to_async(
            lambda: business.products.all().order_by('index')
        )()
            # await MY_METHODS.printStatus(f'Products found: {products.count()} for business: {business.id}')
            productsData = []
            for product in products:
                productData = await PRODUCTS_TASKS.getProduct(product)
                if productData:
                    productsData.append(productData)
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.products_fetch_success,
                code=RESPONSE_CODES.success,
                data=productsData
            )
        except Exception as e:
            # await MY_METHODS.printStatus(f"Error in getProducts: {str(e)}")
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.products_fetch_error,
                code=RESPONSE_CODES.error,
                data={'error':str(e)}
            )
        
    @classmethod
    async def createProduct(self,business:Business,data:dict)->LocalResponse:
        try:
            product = await PRODUCTS_TASKS.createProduct(business,data)
            if not product:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.product_create_error,
                    code=RESPONSE_CODES.error,
                    data={'error':RESPONSE_MESSAGES.product_create_error}
                )
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.product_create_success,
                code=RESPONSE_CODES.success,
                data=product
            )
        except Exception as e:
            # await MY_METHODS.printStatus(f"Error in createProduct: {str(e)}")
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.product_create_error,
                code=RESPONSE_CODES.error,
                data={'error':str(e)}
            )
    
    @classmethod
    async def updateProduct(self,business:Business,productId:int,data:dict)->LocalResponse:
        try:
            product = Product.objects.get(id=productId,business=business)
            if not product:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.product_update_error,
                    code=RESPONSE_CODES.error,
                    data={'error':RESPONSE_MESSAGES.product_update_error}
                )
            product = await PRODUCTS_TASKS.updateProduct(product,data)
            if not product:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.product_update_error,
                    code=RESPONSE_CODES.error,
                    data={'error':RESPONSE_MESSAGES.product_update_error}
                )
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.product_update_success,
                code=RESPONSE_CODES.success,
                data=product
            )
            
        except Exception as e:
            # await MY_METHODS.printStatus(f"Error in updateProduct: {str(e)}")
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.product_update_error,
                code=RESPONSE_CODES.error,
                data={'error':str(e)}
            )
    
    @classmethod
    async def deleteProduct(self,business:Business,productId:int)->LocalResponse:
        try:
            product = Product.objects.get(id=productId,business=business)
            if not product:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.product_delete_error,
                    code=RESPONSE_CODES.error,
                    data={'error':RESPONSE_MESSAGES.product_delete_error}
                )
            product = await PRODUCTS_TASKS.deleteProduct(product)
            if not product:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.product_delete_error,
                    code=RESPONSE_CODES.error,
                    data={'error':RESPONSE_MESSAGES.product_delete_error}
                )
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.product_delete_success,
                code=RESPONSE_CODES.success,
                data=product
            )
        except Exception as e:
            # await MY_METHODS.printStatus(f"Error in deleteProduct: {str(e)}")
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.product_delete_error,
                code=RESPONSE_CODES.error,
                data={'error':str(e)}
            )
        
    @classmethod
    async def GetRelatedProducts(cls, productId: int, page: int = 1, size: int = 10):
        try:
            product = Product.objects.get(id=productId)
            tags = [tag.strip().lower() for tag in product.productTags.split(",")]
            related_qs = Product.objects.filter(
                                Q(title__icontains=product.title.split(" ")[0])
                                | Q(business=product.business)
                            ).exclude(id=product.id).order_by(NAMES.INDEX)

            paginated = await MY_METHODS.paginate_queryset(related_qs, page, size)
            productData = []

            for c in paginated["results"]:
                data = await PRODUCTS_TASKS.getProduct(c)
                if data:
                    productData.append(data)

            paginated['pagination']['data'] = productData

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
            categorys = ProductCategory.objects.all()
            tabData = []
            for category in categorys:
                if category.catProducts.all().count():
                    categoryData = await PRODUCTS_TASKS.getCategoriesDataTask(category)
                    if categoryData:
                        categoryData['type']='category'
                        tabData.append(categoryData)
            subCategorys = ProductSubCategory.objects.all()
            for subCategory in subCategorys:
                if subCategory.subcatProducts.all().count():
                    subCategoryData = await PRODUCTS_TASKS.getCategoriesDataTask(subCategory)
                    if subCategoryData:
                        subCategoryData['type']='subCategory'
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
                data={'error':str(e)}
                )