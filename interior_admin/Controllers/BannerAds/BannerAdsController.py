from asgiref.sync import sync_to_async
from django.db.models import Q
from typing import Any, Dict, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES

from interior_advertisement.models import AdCampaign, AdStatus
from interior_admin.Controllers.Audit.AuditController import append_audit
from .Validators.BannerAdsValidators import BannerAdListFilters, RejectAdSchema


def _ad_dict(c: AdCampaign) -> Dict[str, Any]:
    return {
        "id": c.id, "title": c.title or "Untitled",
        "advertiser": getattr(c.advertiser, "businessName", None) or c.advertiser_id,
        "status": c.status.code if c.status_id else None,
        "priceTotal": float(c.priceTotal), "days": c.days,
        "rejectReason": c.rejectReason,
        "createdAt": c.createdAt.isoformat() if c.createdAt else "",
    }


async def _status(code: str, label: str) -> AdStatus:
    obj, _ = await AdStatus.objects.aget_or_create(code=code, defaults={"label": label})
    return obj


class BannerAdsController:

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def List(cls, queryParams: BannerAdListFilters) -> Tuple[bool, Dict[str, Any]]:
        filters = Q()
        if queryParams.status:
            filters &= Q(status__code=queryParams.status)
        pageNo = max(1, queryParams.pageNo or 1)
        pageSize = min(100, max(1, queryParams.pageSize or 20))
        start = (pageNo - 1) * pageSize
        qs = AdCampaign.objects.filter(filters).select_related("status", "advertiser").order_by("-createdAt")
        total = await qs.acount()
        rows = await sync_to_async(list)(qs[start:start + pageSize])
        return True, {"ads": [_ad_dict(c) for c in rows], "total": total, "pageNo": pageNo, "pageSize": pageSize}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Approve(cls, adId: int, actor=None) -> Tuple[bool, Dict[str, Any]]:
        c = await AdCampaign.objects.select_related("status").filter(id=adId).afirst()
        if c is None:
            return False, {"message": "Ad not found"}
        c.status = await _status("approved", "Approved")
        c.rejectReason = ""
        await sync_to_async(c.save)()
        await append_audit(actor=actor, action="ad_approved", module_key="banners-ad", detail=f"ad={c.id} '{c.title}'")
        c = await AdCampaign.objects.select_related("status", "advertiser").aget(id=adId)
        return True, _ad_dict(c)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Reject(cls, adId: int, payload: RejectAdSchema, actor=None) -> Tuple[bool, Dict[str, Any]]:
        reason = (payload.reason or "").strip()
        if not reason:
            return False, {"message": "A reject reason is required"}
        c = await AdCampaign.objects.select_related("status").filter(id=adId).afirst()
        if c is None:
            return False, {"message": "Ad not found"}
        c.status = await _status("rejected", "Rejected")
        c.rejectReason = reason
        await sync_to_async(c.save)()
        await append_audit(actor=actor, action="ad_rejected", module_key="banners-ad", detail=f"ad={c.id} reason={reason}")
        c = await AdCampaign.objects.select_related("status", "advertiser").aget(id=adId)
        return True, _ad_dict(c)


BANNER_ADS_CONTROLLER = BannerAdsController()
