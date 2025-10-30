from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.MyMethods import MY_METHODS

from .Tasks.productsTasks import PRODUCTS_TASKS
from .Validators.productsValidators import PRODUCTS_VALIDATORS
from app_ib.models import Business
from interior_products.models import Product

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
            #await MY_METHODS.printStatus(f"Error in getProduct: {str(e)}")
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
            #await MY_METHODS.printStatus(f'Products found: {products.count()} for business: {business.id}')
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
            #await MY_METHODS.printStatus(f"Error in getProducts: {str(e)}")
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
            #await MY_METHODS.printStatus(f"Error in createProduct: {str(e)}")
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
            #await MY_METHODS.printStatus(f"Error in updateProduct: {str(e)}")
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
            #await MY_METHODS.printStatus(f"Error in deleteProduct: {str(e)}")
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.product_delete_error,
                code=RESPONSE_CODES.error,
                data={'error':str(e)}
            )