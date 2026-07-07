from adrf.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.decorators.ViewDecorator import exceptionHandler

from interior_admin.Controllers.BannerAds.BannerAdsController import BANNER_ADS_CONTROLLER
from interior_admin.Controllers.BannerAds.Validators.BannerAdsValidators import BannerAdListFilters, RejectAdSchema
from interior_admin.Validators.adminValidators import hasAccess


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def BannerAdsListView(request: Request):
    """GET /api/v1/admin/banners-ad/ — ad campaigns, filter by status code."""
    await hasAccess(request=request)
    return await BANNER_ADS_CONTROLLER.List(queryParams=BannerAdListFilters(**request.query_params.dict()))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def BannerAdApproveView(request: Request, adId: int):
    """POST /api/v1/admin/banners-ad/<id>/approve/ — approve an ad."""
    await hasAccess(request=request)
    return await BANNER_ADS_CONTROLLER.Approve(adId=adId, actor=request.user)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def BannerAdRejectView(request: Request, adId: int):
    """POST /api/v1/admin/banners-ad/<id>/reject/ — reject an ad with a reason."""
    await hasAccess(request=request)
    return await BANNER_ADS_CONTROLLER.Reject(adId=adId, payload=RejectAdSchema(**request.data), actor=request.user)
