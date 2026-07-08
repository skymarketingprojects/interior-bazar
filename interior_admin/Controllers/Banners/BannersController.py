"""Admin House Banners controller.

Targets the REAL home-hero model interior_advertisement.HomeHeroBanner (the one
the public site renders via HomeBannerController) — NOT the dead app_ib.Banners
table the first cut edited. Full nested CRUD over buttons/metrics/businesses,
audience + schedule + background, audited, with public-cache invalidation so
edits show near-live.
"""
from asgiref.sync import sync_to_async
from typing import Any, Dict, List, Optional, Tuple

from django.db import transaction
from django.utils.dateparse import parse_datetime

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES

from interior_advertisement.models import HomeHeroBanner, BannerButton, BannerMetric
from app_ib.Controllers.Engine.HomeBannerController import invalidate_page
from interior_admin.Controllers.Audit.AuditController import append_audit
from .Validators.BannersValidators import (
    BannerCreateSchema, BannerUpdateSchema, BannerMoveSchema)


def _banner_dict(b: HomeHeroBanner) -> Dict[str, Any]:
    """Full admin projection — active + inactive, all nested relations."""
    return {
        "id": b.id,
        "page": b.page,
        "tag": b.tag,
        "title": b.title,
        "description": b.description,
        "audience": b.audience,
        "displayOrder": b.displayOrder,
        "isActive": b.isActive,
        "backgroundGradient": b.backgroundGradient,
        "backgroundImageUrl": b.backgroundImageUrl,
        "startsAt": b.startsAt.isoformat() if b.startsAt else None,
        "endsAt": b.endsAt.isoformat() if b.endsAt else None,
        "buttons": [{"label": x.label, "link": x.link, "isPrimary": x.isPrimary}
                    for x in b.buttons.all()],
        "metrics": [{"metric": m.metric, "description": m.description, "index": m.index}
                    for m in b.metrics.all()],
        "businesses": [{"id": biz.id, "name": biz.businessName} for biz in b.businesses.all()],
    }


def _prefetched(qs):
    return qs.prefetch_related("buttons", "metrics", "businesses")


def _apply(b: HomeHeroBanner, payload, *, partial: bool) -> HomeHeroBanner:
    """Set scalar fields + replace nested buttons/metrics + set businesses M2M.

    Runs synchronously inside a transaction (async ORM can't span M2M writes).
    `partial` (update): skip fields left None so a partial PUT doesn't wipe them;
    (create): apply defaults straight through.
    """
    scalar = ("tag", "title", "description", "page", "displayOrder", "isActive",
              "audience", "backgroundGradient", "backgroundImageUrl")
    with transaction.atomic():
        for f in scalar:
            val = getattr(payload, f)
            if partial and val is None:
                continue
            setattr(b, f, val)
        # Schedule: strings → datetimes; empty/None clears (evergreen).
        if not partial or payload.startsAt is not None:
            b.startsAt = parse_datetime(payload.startsAt) if payload.startsAt else None
        if not partial or payload.endsAt is not None:
            b.endsAt = parse_datetime(payload.endsAt) if payload.endsAt else None
        b.save()

        # Full replace-set of nested relations — the editor always POSTs/PUTs the
        # complete slide state, so an empty array legitimately clears the relation.
        # (Toggle + reorder are dedicated endpoints, never partial PUTs here.)
        b.buttons.all().delete()
        BannerButton.objects.bulk_create([
            BannerButton(banner=b, label=x.label, link=x.link or '', isPrimary=bool(x.isPrimary))
            for x in (payload.buttons or [])])
        b.metrics.all().delete()
        BannerMetric.objects.bulk_create([
            BannerMetric(banner=b, metric=m.metric, description=m.description or '', index=m.index or 0)
            for m in (payload.metrics or [])])
        b.businesses.set((payload.businessIds or [])[:2])
    return b


class BannersController:

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def List(cls, page: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
        qs = HomeHeroBanner.objects.all().order_by("page", "displayOrder", "id")
        if page:
            qs = qs.filter(page=page)
        rows = await sync_to_async(list)(_prefetched(qs))
        data = await sync_to_async(lambda: [_banner_dict(b) for b in rows])()
        return True, {"banners": data}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Create(cls, payload: BannerCreateSchema, actor=None) -> Tuple[bool, Dict[str, Any]]:
        b = HomeHeroBanner()
        b = await sync_to_async(_apply)(b, payload, partial=False)
        await sync_to_async(invalidate_page)(b.page)
        await append_audit(actor=actor, action="banner_created", module_key="banners-house",
                           detail=f"banner={b.id} {b.title} page={b.page}")
        out = await sync_to_async(lambda: _banner_dict(HomeHeroBanner.objects.get(id=b.id)))()
        return True, out

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Update(cls, bannerId: int, payload: BannerUpdateSchema, actor=None) -> Tuple[bool, Dict[str, Any]]:
        b = await HomeHeroBanner.objects.filter(id=bannerId).afirst()
        if b is None:
            return False, {"message": "Banner not found"}
        b = await sync_to_async(_apply)(b, payload, partial=True)
        await sync_to_async(invalidate_page)(b.page)
        await append_audit(actor=actor, action="banner_updated", module_key="banners-house",
                           detail=f"banner={b.id} {b.title} page={b.page}")
        out = await sync_to_async(lambda: _banner_dict(HomeHeroBanner.objects.get(id=b.id)))()
        return True, out

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Toggle(cls, bannerId: int, actor=None) -> Tuple[bool, Dict[str, Any]]:
        b = await HomeHeroBanner.objects.filter(id=bannerId).afirst()
        if b is None:
            return False, {"message": "Banner not found"}
        b.isActive = not b.isActive
        await sync_to_async(b.save)()
        await sync_to_async(invalidate_page)(b.page)
        await append_audit(actor=actor, action=("banner_activated" if b.isActive else "banner_paused"),
                           module_key="banners-house", detail=f"banner={b.id} {b.title}")
        out = await sync_to_async(lambda: _banner_dict(HomeHeroBanner.objects.get(id=b.id)))()
        return True, out

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Delete(cls, bannerId: int, actor=None) -> Tuple[bool, Dict[str, Any]]:
        b = await HomeHeroBanner.objects.filter(id=bannerId).afirst()
        if b is None:
            return False, {"message": "Banner not found"}
        page, title = b.page, b.title
        await sync_to_async(b.delete)()
        await sync_to_async(invalidate_page)(page)
        await append_audit(actor=actor, action="banner_deleted", module_key="banners-house",
                           detail=f"banner={bannerId} {title}")
        return True, {"id": bannerId, "deleted": True}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Move(cls, bannerId: int, payload: BannerMoveSchema, actor=None) -> Tuple[bool, Dict[str, Any]]:
        b = await HomeHeroBanner.objects.filter(id=bannerId).afirst()
        if b is None:
            return False, {"message": "Banner not found"}
        # Swap displayOrder with the adjacent neighbour ON THE SAME PAGE.
        if payload.direction == "up":
            neighbour = await (HomeHeroBanner.objects.filter(page=b.page, displayOrder__lt=b.displayOrder)
                               .order_by("-displayOrder").afirst())
        else:
            neighbour = await (HomeHeroBanner.objects.filter(page=b.page, displayOrder__gt=b.displayOrder)
                               .order_by("displayOrder").afirst())
        if neighbour is not None:
            b.displayOrder, neighbour.displayOrder = neighbour.displayOrder, b.displayOrder
            await sync_to_async(b.save)()
            await sync_to_async(neighbour.save)()
            await sync_to_async(invalidate_page)(b.page)
            await append_audit(actor=actor, action="banner_reordered", module_key="banners-house",
                               detail=f"banner={b.id} {payload.direction}")
        rows = await sync_to_async(list)(_prefetched(
            HomeHeroBanner.objects.all().order_by("page", "displayOrder", "id")))
        data = await sync_to_async(lambda: [_banner_dict(x) for x in rows])()
        return True, {"banners": data}


BANNERS_CONTROLLER = BannersController()
