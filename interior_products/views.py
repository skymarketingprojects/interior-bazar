from rest_framework.permissions import IsAuthenticated, AllowAny
from adrf.views import APIView as AsyncAPIView
from adrf.decorators import api_view
from .Controllers.catelog.catelogController import CATELOG_CONTROLLER
from .Controllers.products.productsController import PRODUCTS_CONTROLLER
from .Controllers.services.servicesController import SERVICES_CONTROLLER
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.models import Business
from django.http import HttpRequest
class ProductView(AsyncAPIView):
    """
    Async class-based view handling GET, POST, PUT, DELETE
    for business catalogs.
    Works with Django + DRF + Uvicorn (ASGI).
    """
    permission_classes = [IsAuthenticated]


    async def get(self, request: HttpRequest,productId: int = None)->ServerResponse:
        try:
            business = None
            productsResponse = None
            if productId == None:
                business = request.user.user_business
                productsResponse = await PRODUCTS_CONTROLLER.getProductsForBusiness(business)
            else:
                productsResponse = await PRODUCTS_CONTROLLER.getProduct(productId)
            return ServerResponse(
                response=productsResponse.response,
                message=productsResponse.message,
                code=productsResponse.code,
                data=productsResponse.data
            )
        except Exception as e:
            await MY_METHODS.printStatus(f'Error in GET: {e}')
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.product_fetch_error,
                code=RESPONSE_CODES.error,
                data={'error': str(e)}
            )
    async def post(self, request: HttpRequest)->ServerResponse:
        try:
            data = MY_METHODS.json_to_object(request.data)
            productsResponse = await PRODUCTS_CONTROLLER.createProduct(request.user.user_business,data)
            return ServerResponse(
                response=productsResponse.response,
                message=productsResponse.message,
                code=productsResponse.code,
                data=productsResponse.data
            )
        except Exception as e:
            await MY_METHODS.printStatus(f'Error in POST: {e}')
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.product_fetch_error,
                code=RESPONSE_CODES.error,
                data={'error': str(e)}
            )
    async def put(self, request: HttpRequest,productId: int)->ServerResponse:
        try:
            data = MY_METHODS.json_to_object(request.data)
            productsResponse = await PRODUCTS_CONTROLLER.updateProduct(request.user.user_business,productId,data)
            return ServerResponse(
                response=productsResponse.response,
                message=productsResponse.message,
                code=productsResponse.code,
                data=productsResponse.data
            )
        except Exception as e:
            await MY_METHODS.printStatus(f'Error in PUT: {e}')
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.catelog_fetch_error,
                code=RESPONSE_CODES.error,
                data={'error': str(e)}
            )
    async def delete(self, request: HttpRequest,productId: int)->ServerResponse:
        try:
            productsResponse = await PRODUCTS_CONTROLLER.deleteProduct(request.user.user_business,productId)
            return ServerResponse(
                response=productsResponse.response,
                message=productsResponse.message,
                code=productsResponse.code,
                data=productsResponse.data
            )
        except Exception as e:
            await MY_METHODS.printStatus(f'Error in DELETE: {e}')
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.catelog_fetch_error,
                code=RESPONSE_CODES.error,
                data={'error': str(e)}
            )
class ServiceView(AsyncAPIView):
    """
    Async class-based view handling GET, POST, PUT, DELETE
    for business catalogs.
    Works with Django + DRF + Uvicorn (ASGI).
    """
    permission_classes = [IsAuthenticated]


    async def get(self, request: HttpRequest,serviceId: int = None)->ServerResponse:
        try:
            business = None
            servicesResponse = None
            if serviceId == None:
                business = request.user.user_business
                servicesResponse = await SERVICES_CONTROLLER.getServicesForBusiness(business)
            else:
                servicesResponse = await SERVICES_CONTROLLER.getService(serviceId)
            return ServerResponse(
                response=servicesResponse.response,
                message=servicesResponse.message,
                code=servicesResponse.code,
                data=servicesResponse.data
            )
        except Exception as e:
            await MY_METHODS.printStatus(f'Error in GET: {e}')
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.service_fetch_error,
                code=RESPONSE_CODES.error,
                data={'error': str(e)}
            )
    async def post(self, request: HttpRequest)->ServerResponse:
        try:
            data = MY_METHODS.json_to_object(request.data)
            servicesResponse = await SERVICES_CONTROLLER.createService(request.user.user_business,data)
            return ServerResponse(
                response=servicesResponse.response,
                message=servicesResponse.message,
                code=servicesResponse.code,
                data=servicesResponse.data
            )
        except Exception as e:
            await MY_METHODS.printStatus(f'Error in POST: {e}')
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.product_fetch_error,
                code=RESPONSE_CODES.error,
                data={'error': str(e)}
            )
    async def put(self, request: HttpRequest,serviceId: int)->ServerResponse:
        try:
            data = MY_METHODS.json_to_object(request.data)
            servicesResponse = await SERVICES_CONTROLLER.updateService(request.user.user_business,serviceId,data)
            return ServerResponse(
                response=servicesResponse.response,
                message=servicesResponse.message,
                code=servicesResponse.code,
                data=servicesResponse.data
            )
        except Exception as e:
            await MY_METHODS.printStatus(f'Error in PUT: {e}')
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.service_fetch_error,
                code=RESPONSE_CODES.error,
                data={'error': str(e)}
            )
    async def delete(self, request: HttpRequest,serviceId: int)->ServerResponse:
        try:
            servicesResponse = await SERVICES_CONTROLLER.deleteService(request.user.user_business,serviceId)
            return ServerResponse(
                response=servicesResponse.response,
                message=servicesResponse.message,
                code=servicesResponse.code,
                data=servicesResponse.data
            )
        except Exception as e:
            await MY_METHODS.printStatus(f'Error in DELETE: {e}')
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.catelog_fetch_error,
                code=RESPONSE_CODES.error,
                data={'error': str(e)}
            )

class CatelogView(AsyncAPIView):
    """
    Async class-based view handling GET, POST, PUT, DELETE
    for business catalogs.
    Works with Django + DRF + Uvicorn (ASGI).
    """
    permission_classes = [IsAuthenticated]


    async def get(self, request, catelogueId: int = None)->ServerResponse:
        """Get all catalogs for a given business."""
        try:
            catelogResponse = None
            business = None
            if catelogueId == None:
                business = request.user.user_business
                catelogResponse = await CATELOG_CONTROLLER.GetCatelogForBusiness(business)
            else:
                catelogResponse = await CATELOG_CONTROLLER.GetCatelog(catelogueId)
            return ServerResponse(
                response=catelogResponse.response,
                message=catelogResponse.message,
                code=catelogResponse.code,
                data=catelogResponse.data
            )
        except Exception as e:
            await MY_METHODS.printStatus(f'Error in GET: {e}')
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.catelog_fetch_error,
                code=RESPONSE_CODES.error,
                data={'error': str(e)}
            )

    async def post(self, request: HttpRequest)->ServerResponse:
        """Create a new catalog for the authenticated business."""
        try:
            user_ins = request.user
            data = MY_METHODS.json_to_object(request.data)
            auth_resp = await CATELOG_CONTROLLER.CreateCatelog(
                business=user_ins.user_business,
                data=data
            )
            return ServerResponse(
                response=auth_resp.response,
                code=auth_resp.code,
                message=auth_resp.message,
                data=auth_resp.data
            )
        except Exception as e:
            await MY_METHODS.printStatus(f'Error in POST: {e}')
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.user_catelog_create_error,
                code=RESPONSE_CODES.error,
                data={'error': str(e)}
            )

    async def put(self, request, catelogueId: int)->ServerResponse:
        """Update an existing catalog."""
        try:
            user_ins = request.user
            data = MY_METHODS.json_to_object(request.data)
            auth_resp = await CATELOG_CONTROLLER.UpdateCatelog(
                business=user_ins.user_business,
                catelogId=catelogueId,
                data=data
            )
            return ServerResponse(
                response=auth_resp.response,
                code=auth_resp.code,
                message=auth_resp.message,
                data=auth_resp.data
            )
        except Exception as e:
            await MY_METHODS.printStatus(f'Error in PUT: {e}')
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.user_catelog_update_error,
                code=RESPONSE_CODES.error,
                data={'error': str(e)}
            )

    async def delete(self, request, catelogueId: int)->ServerResponse:
        """Delete a catalog."""
        try:
            user_ins = request.user
            auth_resp = await CATELOG_CONTROLLER.DeleteCatelog(
                business=user_ins.user_business,
                catelogId=catelogueId
            )
            return ServerResponse(
                response=auth_resp.response,
                code=auth_resp.code,
                message=auth_resp.message,
                data=auth_resp.data
            )
        except Exception as e:
            await MY_METHODS.printStatus(f'Error in DELETE: {e}')
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.catelog_deleted_error,
                code=RESPONSE_CODES.error,
                data={'error': str(e)}
            )
@api_view(['GET'])
async def GetBusinessCatelogs(request, businessId: int)->ServerResponse:
    """Get all catalogs for a given business."""
    try:
        await MY_METHODS.printStatus(f'GetBusinessCatelogs: {businessId} type: {type(businessId)}')
        business = Business.objects.get(id=businessId)
        await MY_METHODS.printStatus(f'Business fetched: {business}')
        catelogResponse = await CATELOG_CONTROLLER.GetCatelogForBusiness(business)
        return ServerResponse(
            response=catelogResponse.response,
            message=catelogResponse.message,
            code=catelogResponse.code,
            data=catelogResponse.data
        )
    except Exception as e:
        await MY_METHODS.printStatus(f'Error in catelog GET: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.catelog_fetch_error,
            code=RESPONSE_CODES.error,
            data={'error': str(e)}
        )
    
@api_view(['GET'])
async def GetBusinessProducts(request, businessId: int)->ServerResponse:
    """Get all products for a given business."""
    try:
        
        business = Business.objects.get(id=businessId)
        productsResponse = await PRODUCTS_CONTROLLER.getProductsForBusiness(business)
        await MY_METHODS.printStatus(f'Products fetched: {productsResponse}')
        return ServerResponse(
            response=productsResponse.response,
            message=productsResponse.message,
            code=productsResponse.code,
            data=productsResponse.data
        )
    except Exception as e:
        await MY_METHODS.printStatus(f'Error in product GET: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.product_fetch_error,
            code=RESPONSE_CODES.error,
            data={'error': str(e)}
        )
@api_view(['GET'])
async def GetBusinessServices(request, businessId: int)->ServerResponse:
    """Get all products for a given business."""
    try:
        
        business = Business.objects.get(id=businessId)
        servicesResponse = await SERVICES_CONTROLLER.getServicesForBusiness(business)
        return ServerResponse(
            response=servicesResponse.response,
            message=servicesResponse.message,
            code=servicesResponse.code,
            data=servicesResponse.data
        )
    except Exception as e:
        await MY_METHODS.printStatus(f'Error in service GET: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.product_fetch_error,
            code=RESPONSE_CODES.error,
            data={'error': str(e)}
        )