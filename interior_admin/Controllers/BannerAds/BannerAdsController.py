from asgiref.sync import sync_to_async
from django.db.models import Q, Max
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from typing import Any, Dict, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES

from interior_advertisement.models import (
    AdCampaign, AdStatus, AdAsset, AdPlacement, AdApprovalMode, AdAssetType,
)
from app_ib.Controllers.Engine.GapsController import _ad_creative
from interior_admin.Controllers.Audit.AuditController import append_audit
from .Validators.BannerAdsValidators import BannerAdListFilters, RejectAdSchema, FallbackAdSchema

# Admin tabs → real AdStatus codes. pending review = 'draft' (created state),
# live = 'active' (NAMES.ACTIVE, the code the public render path filters on),
# rejected = 'rejected'.
TAB_STATUS = {"pending": "draft", "live": "active", "rejected": "rejected"}


def _ad_dict(c: AdCampaign) -> Dict[str, Any]:
    assets = list(c.assets.all())
    creative = _ad_creative(assets[0] if assets else None)
    days = c.days or 0
    return {
        "id": c.id, "title": c.title or "Untitled",
        "advertiser": getattr(c.advertiser, "businessName", None) or c.advertiser_id or "House ad",
        "isHouseAd": not c.advertiser_id,
        "page": c.page or "",
        "status": c.status.code if c.status_id else None,
        "priceTotal": float(c.priceTotal), "days": days,
        "months": max(1, round(days / 30)) if days else 0,
        "spots": [c.placement.code] if c.placement_id else [],
        "creative": creative,
        "rejectReason": c.rejectReason,
        "createdAt": c.createdAt.isoformat() if c.createdAt else "",
    }


async def _status(code: str, label: str) -> AdStatus:
    obj, _ = await AdStatus.objects.aget_or_create(code=code, defaults={"label": label})
    return obj


async def _approval_mode(code: str, label: str) -> AdApprovalMode:
    obj, _ = await AdApprovalMode.objects.aget_or_create(code=code, defaults={"label": label})
    return obj


async def _asset_type(code: str, label: str) -> AdAssetType:
    obj, _ = await AdAssetType.objects.aget_or_create(code=code, defaults={"label": label})
    return obj


async def _placement(code: str) -> AdPlacement:
    obj = await AdPlacement.objects.filter(code=code).afirst()
    if obj:
        return obj
    # placementId is a manual PK — assign the next free id for a new house placement.
    agg = await AdPlacement.objects.aaggregate(m=Max("placementId"))
    nid = (agg["m"] or 0) + 1
    return await AdPlacement.objects.acreate(
        placementId=nid, code=code, dailyPrice=Decimal("0.00"), aspectRatio="1:1"
    )


class BannerAdsController:

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def List(cls, queryParams: BannerAdListFilters) -> Tuple[bool, Dict[str, Any]]:
        filters = Q()
        if queryParams.status:
            # Accept either a tab key (pending/live/rejected) or a raw status code.
            code = TAB_STATUS.get(queryParams.status, queryParams.status)
            filters &= Q(status__code=code)
        pageNo = max(1, queryParams.pageNo or 1)
        pageSize = min(100, max(1, queryParams.pageSize or 20))
        start = (pageNo - 1) * pageSize
        qs = (AdCampaign.objects.filter(filters)
              .select_related("status", "advertiser", "placement")
              .prefetch_related("assets")
              .order_by("-createdAt"))
        total = await qs.acount()
        rows = await sync_to_async(list)(qs[start:start + pageSize])
        counts = {
            "pending": await AdCampaign.objects.filter(status__code="draft").acount(),
            "live": await AdCampaign.objects.filter(status__code="active").acount(),
            "rejected": await AdCampaign.objects.filter(status__code="rejected").acount(),
        }
        return True, {
            "ads": await sync_to_async(lambda: [_ad_dict(c) for c in rows])(),
            "counts": counts, "total": total, "pageNo": pageNo, "pageSize": pageSize,
        }

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Approve(cls, adId: int, actor=None) -> Tuple[bool, Dict[str, Any]]:
        c = await AdCampaign.objects.select_related("status").filter(id=adId).afirst()
        if c is None:
            return False, {"message": "Ad not found"}
        # Approve → 'active' (the code the public render path filters on) so an
        # approved ad actually goes live. (Was 'approved', which rendered nowhere.)
        c.status = await _status("active", "Active")
        c.rejectReason = ""
        await sync_to_async(c.save)()
        await append_audit(actor=actor, action="ad_approved", module_key="banners-ad", detail=f"ad={c.id} '{c.title}'")
        return True, await cls._reload(adId)

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
        return True, await cls._reload(adId)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def CreateFallback(cls, payload: FallbackAdSchema, actor=None) -> Tuple[bool, Dict[str, Any]]:
        # House/fallback ad = an AdCampaign with no business advertiser that
        # auto-approves to 'active' and shows when no paid ad fills the slot.
        placement = await _placement(payload.placement)
        status = await _status("active", "Active")
        mode = await _approval_mode("auto", "Auto approve")
        asset_type = await _asset_type("image", "Image Asset")
        now = timezone.now()
        c = await AdCampaign.objects.acreate(
            advertiser=None,
            title=(payload.heading or payload.eyebrow or "House ad"),
            page=(payload.page or ""),
            placement=placement,
            startDate=now, endDate=now + timedelta(days=3650), days=3650,
            priceTotal=Decimal("0.00"), status=status, approvalMode=mode,
        )
        meta = {
            "eyebrow": payload.eyebrow or "", "heading1": payload.heading or "",
            "description": payload.sub or "", "features": payload.features or [],
            "buttonLabel": payload.ctaLabel or "", "buttonLink": payload.ctaLink or "",
            "theme": payload.theme or "green",
        }
        await AdAsset.objects.acreate(
            campaign=c, assetType=asset_type, s3Key=(payload.image or ""), meta=meta,
        )
        await append_audit(actor=actor, action="ad_fallback_created", module_key="banners-ad",
                           detail=f"ad={c.id} page={c.page} placement={payload.placement}")
        return True, await cls._reload(c.id)

    @classmethod
    async def _reload(cls, adId: int) -> Dict[str, Any]:
        c = await sync_to_async(
            lambda: AdCampaign.objects.select_related("status", "advertiser", "placement")
            .prefetch_related("assets").get(id=adId)
        )()
        return await sync_to_async(_ad_dict)(c)


BANNER_ADS_CONTROLLER = BannerAdsController()
