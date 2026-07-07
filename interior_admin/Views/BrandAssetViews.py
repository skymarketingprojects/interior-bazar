from adrf.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.decorators.ViewDecorator import exceptionHandler

from interior_admin.Controllers.BrandAsset.BrandAssetController import BRAND_ASSET_CONTROLLER
from interior_admin.Controllers.BrandAsset.Validators.BrandAssetValidators import BrandAssetSchema
from interior_admin.Validators.adminValidators import hasAccess


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def BrandLogoView(request: Request):
    """GET /api/v1/admin/brand-logo/ — current brand assets.
    PUT /api/v1/admin/brand-logo/ — set logoUrl/faviconUrl (S3 URLs uploaded
    client-side). Level-3 (audited)."""
    await hasAccess(request=request)
    if request.method == 'PUT':
        return await BRAND_ASSET_CONTROLLER.Set(payload=BrandAssetSchema(**request.data), actor=request.user)
    return await BRAND_ASSET_CONTROLLER.Get()
