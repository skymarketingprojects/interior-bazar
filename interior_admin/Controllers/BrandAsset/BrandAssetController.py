from asgiref.sync import sync_to_async
from datetime import date
from typing import Any, Dict, Tuple

from django.utils import timezone

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES

from interior_admin.models import BrandAsset, BrandLogo
from interior_admin.Controllers.Audit.AuditController import append_audit
from .Validators.BrandAssetValidators import BrandAssetSchema, BrandLogoCreateSchema, BrandLogoUpdateSchema


def _brand_dict(b: BrandAsset) -> Dict[str, Any]:
    return {"logoUrl": b.logoUrl, "faviconUrl": b.faviconUrl, "tagline": b.tagline,
            "updatedAt": b.updatedAt.isoformat() if b.updatedAt else ""}


def _logo_dict(l: BrandLogo) -> Dict[str, Any]:
    return {"id": l.id, "label": l.label, "imageUrl": l.imageUrl, "tagline": l.tagline,
            "activeFrom": l.activeFrom.isoformat() if l.activeFrom else "",
            "activeTo": l.activeTo.isoformat() if l.activeTo else "",
            "createdAt": l.createdAt.isoformat() if l.createdAt else ""}


def _parse_date(s):
    """'' / None → None; 'YYYY-MM-DD' → date. Anything unparseable → None."""
    if not s:
        return None
    try:
        return date.fromisoformat(str(s)[:10])
    except ValueError:
        return None


def resolve_active_logo() -> Dict[str, str]:
    """Pure sync resolver — today's winning brand logo + tagline (task 27).
    Priority: an active DATED entry (winner = latest activeFrom, tie-break latest
    createdAt) → an always-on unbounded entry (latest createdAt) → BrandAsset
    default. Uses timezone.localdate() so windows are evaluated in server-local time."""
    today = timezone.localdate()
    logos = list(BrandLogo.objects.all())

    def is_active(l: BrandLogo) -> bool:
        if l.activeFrom and l.activeFrom > today:
            return False
        if l.activeTo and l.activeTo < today:
            return False
        return True

    live = [l for l in logos if is_active(l)]
    dated = [l for l in live if l.activeFrom or l.activeTo]
    if dated:
        winner = max(dated, key=lambda l: (l.activeFrom or date.min, l.createdAt))
        return {"logoUrl": winner.imageUrl, "tagline": winner.tagline}
    unbounded = [l for l in live if not l.activeFrom and not l.activeTo]
    if unbounded:
        winner = max(unbounded, key=lambda l: l.createdAt)
        return {"logoUrl": winner.imageUrl, "tagline": winner.tagline}
    b = BrandAsset.objects.filter(id=1).first()
    return {"logoUrl": b.logoUrl if b else "", "tagline": (b.tagline if b else "") or ""}


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
        if payload.tagline is not None:
            b.tagline = payload.tagline; changed.append("tagline")
        await sync_to_async(b.save)()
        await append_audit(actor=actor, action='brand_asset_updated', module_key='brand-logo',
                           detail=f"updated={','.join(changed) or 'none'}")
        return True, _brand_dict(b)

    # ── scheduled logos (task 27) ──
    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def ListLogos(cls) -> Tuple[bool, Dict[str, Any]]:
        rows = await sync_to_async(list)(BrandLogo.objects.all())
        active = await sync_to_async(resolve_active_logo)()
        return True, {"logos": [_logo_dict(l) for l in rows], "active": active}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def CreateLogo(cls, payload: BrandLogoCreateSchema, actor=None) -> Tuple[bool, Dict[str, Any]]:
        l = await BrandLogo.objects.acreate(
            label=payload.label or '', imageUrl=payload.imageUrl, tagline=payload.tagline or '',
            activeFrom=_parse_date(payload.activeFrom), activeTo=_parse_date(payload.activeTo))
        await append_audit(actor=actor, action='brand_logo_created', module_key='brand-logo', detail=f"logo={l.id}")
        return True, _logo_dict(l)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def UpdateLogo(cls, logoId: int, payload: BrandLogoUpdateSchema, actor=None) -> Tuple[bool, Dict[str, Any]]:
        l = await BrandLogo.objects.filter(id=logoId).afirst()
        if l is None:
            return False, {"message": "Logo not found"}
        if payload.label is not None:
            l.label = payload.label
        if payload.imageUrl is not None:
            l.imageUrl = payload.imageUrl
        if payload.tagline is not None:
            l.tagline = payload.tagline
        if payload.activeFrom is not None:
            l.activeFrom = _parse_date(payload.activeFrom)
        if payload.activeTo is not None:
            l.activeTo = _parse_date(payload.activeTo)
        await sync_to_async(l.save)()
        await append_audit(actor=actor, action='brand_logo_updated', module_key='brand-logo', detail=f"logo={l.id}")
        return True, _logo_dict(l)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def DeleteLogo(cls, logoId: int, actor=None) -> Tuple[bool, Dict[str, Any]]:
        l = await BrandLogo.objects.filter(id=logoId).afirst()
        if l is None:
            return False, {"message": "Logo not found"}
        await sync_to_async(l.delete)()
        await append_audit(actor=actor, action='brand_logo_deleted', module_key='brand-logo', detail=f"logo={logoId}")
        return True, {"id": logoId, "deleted": True}


BRAND_ASSET_CONTROLLER = BrandAssetController()
