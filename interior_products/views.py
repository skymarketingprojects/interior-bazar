from rest_framework.permissions import IsAuthenticated, AllowAny
from adrf.views import APIView as AsyncAPIView
from adrf.decorators import api_view
from .Controllers.catelog.catelogController import CATELOG_CONTROLLER
from .Controllers.products.productsController import PRODUCTS_CONTROLLER
from interior_business.Controllers.Business.BusinessController import BUSS_CONTROLLER
from .Controllers.services.servicesController import SERVICES_CONTROLLER
from .Controllers.InteriorService.InteriorServiceController import INTERIOR_SERVICE_CONTROLLER
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.models import Business
from django.http import HttpRequest
from app_ib.Utils.Names import NAMES
from django.core.cache import cache
from asgiref.sync import sync_to_async

cache_get = sync_to_async(cache.get)
cache_set = sync_to_async(cache.set)

# 30 mins TTL for items/marketplace data
PRODUCT_TTL = 1800
# 7 days for static structural data
STATIC_TTL = 604800

class ProductView(AsyncAPIView):
    """
    Async class-based view handling GET, POST, PUT, DELETE
    for business catalogs.
    Works with Django + DRF + Uvicorn (ASGI).
    """
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == 'GET':
            self.permission_classes = [AllowAny]
        return super().get_permissions()


    async def get(self, request: HttpRequest,productId: int = None)->ServerResponse:
        try:
            business = None
            productsResponse = None
            cache_key = None
            
            if productId == None:
                business = request.user.user_business
                cache_key = f"cache:product:business:owner:{business.id}"
            else:
                cache_key = f"cache:product:{productId}"
            
            cached_data = await cache_get(cache_key)
            if cached_data:
                return ServerResponse(**cached_data)

            if productId == None:
                productsResponse = await PRODUCTS_CONTROLLER.getProductsForBusiness(business)
            else:
                productsResponse = await PRODUCTS_CONTROLLER.getProduct(productId)
            
            resp_dict = {
                'response': productsResponse.response,
                'message': productsResponse.message,
                'code': productsResponse.code,
                'data': productsResponse.data
            }
            await cache_set(cache_key, resp_dict, timeout=PRODUCT_TTL)

            return ServerResponse(**resp_dict)
        except Exception as e:
            pass
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
            pass
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
            pass
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
            pass
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

    def get_permissions(self):
        if self.request.method == 'GET':
            self.permission_classes = [AllowAny]
        return super().get_permissions()


    async def get(self, request: HttpRequest,serviceId: int = None)->ServerResponse:
        try:
            business = None
            servicesResponse = None
            cache_key = None

            if serviceId == None:
                business = request.user.user_business
                cache_key = f"cache:service:business:owner:{business.id}"
            else:
                cache_key = f"cache:service:{serviceId}"
            
            cached_data = await cache_get(cache_key)
            if cached_data:
                return ServerResponse(**cached_data)

            if serviceId == None:
                servicesResponse = await SERVICES_CONTROLLER.getServicesForBusiness(business)
            else:
                servicesResponse = await SERVICES_CONTROLLER.getService(serviceId)

            resp_dict = {
                'response': servicesResponse.response,
                'message': servicesResponse.message,
                'code': servicesResponse.code,
                'data': servicesResponse.data
            }
            await cache_set(cache_key, resp_dict, timeout=PRODUCT_TTL)

            return ServerResponse(**resp_dict)
        except Exception as e:
            pass
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
            pass
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
            pass
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
            pass
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

    def get_permissions(self):
        if self.request.method == 'GET':
            self.permission_classes = [AllowAny]
        return super().get_permissions()


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
            pass
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
            pass
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
            pass
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
            pass
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
        business = Business.objects.get(id=businessId)
        catelogResponse = await CATELOG_CONTROLLER.GetCatelogForBusiness(business)
        
        return ServerResponse(
            response=catelogResponse.response,
            message=catelogResponse.message,
            code=catelogResponse.code,
            data=catelogResponse.data
        )
    except Exception as e:
        pass
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
        cache_key = f"cache:product:business:{businessId}"
        cached_data = await cache_get(cache_key)
        if cached_data:
            return ServerResponse(**cached_data)

        business = Business.objects.get(id=businessId)
        productsResponse = await PRODUCTS_CONTROLLER.getProductsForBusiness(business)
        
        resp_dict = {
            'response': productsResponse.response,
            'message': productsResponse.message,
            'code': productsResponse.code,
            'data': productsResponse.data
        }
        await cache_set(cache_key, resp_dict, timeout=PRODUCT_TTL)
        return ServerResponse(**resp_dict)
    except Exception as e:
        pass
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
        cache_key = f"cache:service:business:{businessId}"
        cached_data = await cache_get(cache_key)
        if cached_data:
            return ServerResponse(**cached_data)

        business = Business.objects.get(id=businessId)
        servicesResponse = await SERVICES_CONTROLLER.getServicesForBusiness(business)
        
        resp_dict = {
            'response': servicesResponse.response,
            'message': servicesResponse.message,
            'code': servicesResponse.code,
            'data': servicesResponse.data
        }
        await cache_set(cache_key, resp_dict, timeout=PRODUCT_TTL)
        return ServerResponse(**resp_dict)
    except Exception as e:
        pass
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.product_fetch_error,
            code=RESPONSE_CODES.error,
            data={'error': str(e)}
        )


@api_view(['GET'])
async def GetRelatedCatelogs(request, catelogId: int)->ServerResponse:
    try:
        page = int(request.query_params.get('pageNo', 1))
        size = int(request.query_params.get('pageSize', 10))

        resp = await CATELOG_CONTROLLER.GetRelatedCatelogs(catelogId, page, size)
        
        return ServerResponse(
            response=resp.response,
            message=resp.message,
            code=resp.code,
            data=resp.data
        )
    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message="Error fetching related catelogues",
            code=RESPONSE_CODES.error,
            data={'error': str(e)}
        )

@api_view(['GET'])
async def GetRelatedProducts(request, productId: int)->ServerResponse:
    try:
        page = int(request.query_params.get('pageNo', 1))
        size = int(request.query_params.get('pageSize', 10))
        cache_key = f"cache:product:related:{productId}:p{page}:s{size}"
        cached_data = await cache_get(cache_key)
        if cached_data:
            return ServerResponse(**cached_data)

        resp = await PRODUCTS_CONTROLLER.GetRelatedProducts(productId, page, size)
        
        resp_dict = {
            'response': resp.response,
            'message': resp.message,
            'code': resp.code,
            'data': resp.data
        }
        await cache_set(cache_key, resp_dict, timeout=PRODUCT_TTL)
        return ServerResponse(**resp_dict)
    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message="Error fetching related products",
            code=RESPONSE_CODES.error,
            data={'error': str(e)}
        )

@api_view(['GET'])
async def GetRelatedServices(request, serviceId: int)->ServerResponse:
    try:
        page = int(request.query_params.get('pageNo', 1))
        size = int(request.query_params.get('pageSize', 10))
        cache_key = f"cache:service:related:{serviceId}:p{page}:s{size}"
        cached_data = await cache_get(cache_key)
        if cached_data:
            return ServerResponse(**cached_data)

        resp = await SERVICES_CONTROLLER.GetRelatedServices(serviceId, page, size)
        
        resp_dict = {
            'response': resp.response,
            'message': resp.message,
            'code': resp.code,
            'data': resp.data
        }
        await cache_set(cache_key, resp_dict, timeout=PRODUCT_TTL)
        return ServerResponse(**resp_dict)
    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message="Error fetching related services",
            code=RESPONSE_CODES.error,
            data={'error': str(e)}
        )

# get all
@api_view(['GET'])
async def GetAllCatelogsView(request):
    try:
        pageNo= int(request.query_params.get("pageNo",1))
        pageSize = int(request.query_params.get('pageSize',10))
        filterType = request.query_params.get('type',None)
        filterId = request.query_params.get('tabId',None)
        state = request.query_params.get('state',None)
        query = request.query_params.get('query',None)
        
        catelogResponse = await CATELOG_CONTROLLER.GetAllCatelog(page=pageNo,size=pageSize,filterType=filterType,id=filterId,state=state,query=query)
        
        return ServerResponse(
            response=catelogResponse.response,
            message=catelogResponse.message,
            code=catelogResponse.code,
            data=catelogResponse.data
        )
    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message="Error fetching catelogues",
            code=RESPONSE_CODES.error,
            data={'error': str(e)}
        )

@api_view(['GET'])
async def GetAllProductView(request:HttpRequest):
    try:
        pageNo= int(request.GET.get("pageNo",1))
        pageSize = int(request.GET.get('pageSize',10))
        filterType = request.GET.get('type',None)
        filterId = request.GET.get('tabId',None)
        state = request.GET.get('state',None)
        query = request.GET.get('query',None)

        cache_key = f"cache:product:all:p{pageNo}:s{pageSize}:t{filterType}:id{filterId}:st{state}:q{query}"
        cached_data = await cache_get(cache_key)
        if cached_data:
            return ServerResponse(**cached_data)

        catelogResponse = await PRODUCTS_CONTROLLER.getAllProduct(page=pageNo,size=pageSize,filterType=filterType,id=filterId,state=state,query=query)
        
        resp_dict = {
            'response': catelogResponse.response,
            'message': catelogResponse.message,
            'code': catelogResponse.code,
            'data': catelogResponse.data
        }
        await cache_set(cache_key, resp_dict, timeout=PRODUCT_TTL)
        return ServerResponse(**resp_dict)
    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message="Error fetching product",
            code=RESPONSE_CODES.error,
            data={'error': str(e)}
        )

@api_view(['GET'])
async def GetAllServiceView(request:HttpRequest):
    try:
        pageNo= int(request.GET.get("pageNo",1))
        pageSize = int(request.GET.get('pageSize',10))
        filterType = request.GET.get('type',None)
        filterId = request.GET.get('tabId',None)
        state = request.GET.get('state',None)
        query = request.GET.get('query',None)

        cache_key = f"cache:service:all:p{pageNo}:s{pageSize}:t{filterType}:id{filterId}:st{state}:q{query}"
        cached_data = await cache_get(cache_key)
        if cached_data:
            return ServerResponse(**cached_data)

        catelogResponse = await SERVICES_CONTROLLER.getAllService(page=pageNo,size=pageSize,filterType=filterType,id=filterId,state=state,query=query)
        
        resp_dict = {
            'response': catelogResponse.response,
            'message': catelogResponse.message,
            'code': catelogResponse.code,
            'data': catelogResponse.data
        }
        await cache_set(cache_key, resp_dict, timeout=PRODUCT_TTL)
        return ServerResponse(**resp_dict)
    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message="Error fetching Services",
            code=RESPONSE_CODES.error,
            data={'error': str(e)}
        )

@api_view(['GET'])
async def GetOwnServicesView(request:HttpRequest):
    try:
        pageNo= int(request.GET.get("pageNo",1))
        pageSize = int(request.GET.get('pageSize',10))
        
        cache_key = f"cache:service:own:p{pageNo}:s{pageSize}"
        cached_data = await cache_get(cache_key)
        if cached_data:
            return ServerResponse(**cached_data)

        catelogResponse = await INTERIOR_SERVICE_CONTROLLER.getInteriorService(pageNo=pageNo,pageSize=pageSize)
        
        resp_dict = {
            'response': catelogResponse.response,
            'message': catelogResponse.message,
            'code': catelogResponse.code,
            'data': catelogResponse.data
        }
        await cache_set(cache_key, resp_dict, timeout=PRODUCT_TTL)
        return ServerResponse(**resp_dict)
    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message="Error fetching Services",
            code=RESPONSE_CODES.error,
            data={'error': str(e)}
        )
# categories
@api_view(['GET'])
async def GetProductCategoriesView(request):
    try:
        cache_key = "cache:product:categories"
        cached_data = await cache_get(cache_key)
        if cached_data:
            return ServerResponse(**cached_data)

        resp = await PRODUCTS_CONTROLLER.GetProductCategories()
        
        resp_dict = {
            'response': resp.response,
            'message': resp.message,
            'code': resp.code,
            'data': resp.data
        }
        await cache_set(cache_key, resp_dict, timeout=STATIC_TTL)
        return ServerResponse(**resp_dict)
    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message="Error fetching Categories",
            code=RESPONSE_CODES.error,
            data={'error': str(e)}
        )

@api_view(['GET'])
async def GetProductSubCategoriesView(request):
    try:
        cache_key = "cache:product:sub_categories"
        cached_data = await cache_get(cache_key)
        if cached_data:
            return ServerResponse(**cached_data)

        resp = await PRODUCTS_CONTROLLER.GetProductSubCategories()
        
        resp_dict = {
            'response': resp.response,
            'message': resp.message,
            'code': resp.code,
            'data': resp.data
        }
        await cache_set(cache_key, resp_dict, timeout=STATIC_TTL)
        return ServerResponse(**resp_dict)
    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message="Error fetching Sub Categories",
            code=RESPONSE_CODES.error,
            data={'error': str(e)}
        )
    
@api_view(['GET'])
async def GetTabsView(request):
    try:
        filterFor= request.GET.get('type')
        
        cache_key = f"cache:product:tabs:{filterFor}"
        cached_data = await cache_get(cache_key)
        if cached_data:
            return ServerResponse(**cached_data)

        resp=None
        functionList={
            'product':PRODUCTS_CONTROLLER.GetProductTab,
            'service':SERVICES_CONTROLLER.GetServiceTab,
            'catelouge':CATELOG_CONTROLLER.GetCatelougeTab,
            'business':BUSS_CONTROLLER.GetAllBusinessTab
        }
        if filterFor in functionList:
            resp= await functionList[filterFor]()
        else:
            resp= await CATELOG_CONTROLLER.GetCatelougeTab()
        
        resp.data.sort(
                key=lambda x: (x.get(NAMES.LABEL) or "").lower()
            )

        return ServerResponse(
            response=resp.response,
            message=resp.message,
            code=resp.code,
            data=resp.data
        )
    except Exception as e:
        pass
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message="Error fetching Tabs",
            code=RESPONSE_CODES.error,
            data={'error': str(e)}
        )