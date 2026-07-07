from asgiref.sync import sync_to_async
from typing import Any, Dict, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES

from interior_admin.models import BrandAsset
from interior_admin.Controllers.Audit.AuditController import append_audit
from .Validators.BrandAssetValidators import BrandAssetSchema


def _brand_dict(b: BrandAsset) -> Dict[str, Any]:
    return {"logoUrl": b.logoUrl, "faviconUrl": b.faviconUrl,
            "updatedAt": b.updatedAt.isoformat() if b.updatedAt else ""}


class BrandAssetController:

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Get(cls) -> Tuple[bool, Dict[str, Any]]:
        b, _ = await BrandAsset.objects.aget_or_create(id=1)
        return True, _brand_dict(b)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Set(cls, payload: BrandAssetSchema, actor=None) -> Tuple[bool, Dict[str, Any]]:
        b, _ = await BrandAsset.objects.aget_or_create(id=1)
        changed = []
        if payload.logoUrl is not None:
            b.logoUrl = payload.logoUrl; changed.append("logo")
        if payload.faviconUrl is not None:
            b.faviconUrl = payload.faviconUrl; changed.append("favicon")
        await sync_to_async(b.save)()
        await append_audit(actor=actor, action='brand_asset_updated', module_key='brand-logo',
                           detail=f"updated={','.join(changed) or 'none'}")
        return True, _brand_dict(b)


BRAND_ASSET_CONTROLLER = BrandAssetController()
