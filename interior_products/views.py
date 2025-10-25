from rest_framework.permissions import IsAuthenticated, AllowAny
from adrf.views import APIView as AsyncAPIView
from adrf.decorators import api_view
from .Controllers.catelog.catelogController import CATELOG_CONTROLLER
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.models import Business

class CatelogView(AsyncAPIView):
    """
    Async class-based view handling GET, POST, PUT, DELETE
    for business catalogs.
    Works with Django + DRF + Uvicorn (ASGI).
    """
    permission_classes = [IsAuthenticated]


    async def get(self, request, catelogueId: int = None, *args, **kwargs):
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

    async def post(self, request, *args, **kwargs):
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

    async def put(self, request, catelogueId: int, *args, **kwargs):
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

    async def delete(self, request, catelogueId: int, *args, **kwargs):
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
async def GetBusinessCatelogs(request, businessId: int):
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
        await MY_METHODS.printStatus(f'Error in GET: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.catelog_fetch_error,
            code=RESPONSE_CODES.error,
            data={'error': str(e)}
        )