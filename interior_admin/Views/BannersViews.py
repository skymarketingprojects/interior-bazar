from adrf.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.decorators.ViewDecorator import exceptionHandler

from interior_admin.Controllers.Banners.BannersController import BANNERS_CONTROLLER
from interior_admin.Controllers.Banners.Validators.BannersValidators import (
    BannerCreateSchema, BannerUpdateSchema, BannerMoveSchema)
from interior_admin.Validators.adminValidators import hasAccess


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def BannersCollectionView(request: Request):
    """GET/POST /api/v1/admin/banners-house/ — list / create house banners."""
    await hasAccess(request=request)
    if request.method == 'POST':
        return await BANNERS_CONTROLLER.Create(payload=BannerCreateSchema(**request.data))
    return await BANNERS_CONTROLLER.List()


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def BannerDetailView(request: Request, bannerId: int):
    """PUT/DELETE /api/v1/admin/banners-house/<id>/ — edit / delete."""
    await hasAccess(request=request)
    if request.method == 'DELETE':
        return await BANNERS_CONTROLLER.Delete(bannerId=bannerId)
    return await BANNERS_CONTROLLER.Update(bannerId=bannerId, payload=BannerUpdateSchema(**request.data))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def BannerMoveView(request: Request, bannerId: int):
    """POST /api/v1/admin/banners-house/<id>/move/ — reorder up/down."""
    await hasAccess(request=request)
    return await BANNERS_CONTROLLER.Move(bannerId=bannerId, payload=BannerMoveSchema(**request.data))
