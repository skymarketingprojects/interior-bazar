from asgiref.sync import sync_to_async
from typing import Any, Dict, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES

from app_ib.models import Banners
from .Validators.BannersValidators import BannerCreateSchema, BannerUpdateSchema, BannerMoveSchema


def _banner_dict(b: Banners) -> Dict[str, Any]:
    img = b.bannerUrl or (b.banner.url if b.banner else "")
    return {"id": b.id, "title": b.title, "supportText": b.supportText,
            "bannerUrl": img, "order": b.order, "isActive": b.isActive}


class BannersController:

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def List(cls) -> Tuple[bool, Dict[str, Any]]:
        rows = await sync_to_async(list)(Banners.objects.all())
        return True, {"banners": [_banner_dict(b) for b in rows]}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Create(cls, payload: BannerCreateSchema) -> Tuple[bool, Dict[str, Any]]:
        last = await Banners.objects.order_by("-order").afirst()
        nxt = (last.order + 1) if last else 0
        b = await Banners.objects.acreate(
            title=payload.title, supportText=payload.supportText or '',
            bannerUrl=payload.bannerUrl or '', isActive=bool(payload.isActive), order=nxt)
        return True, _banner_dict(b)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Update(cls, bannerId: int, payload: BannerUpdateSchema) -> Tuple[bool, Dict[str, Any]]:
        b = await Banners.objects.filter(id=bannerId).afirst()
        if b is None:
            return False, {"message": "Banner not found"}
        for f in ("title", "supportText", "bannerUrl", "isActive"):
            val = getattr(payload, f)
            if val is not None:
                setattr(b, f, val)
        await sync_to_async(b.save)()
        return True, _banner_dict(b)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Delete(cls, bannerId: int) -> Tuple[bool, Dict[str, Any]]:
        b = await Banners.objects.filter(id=bannerId).afirst()
        if b is None:
            return False, {"message": "Banner not found"}
        await sync_to_async(b.delete)()
        return True, {"id": bannerId, "deleted": True}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Move(cls, bannerId: int, payload: BannerMoveSchema) -> Tuple[bool, Dict[str, Any]]:
        b = await Banners.objects.filter(id=bannerId).afirst()
        if b is None:
            return False, {"message": "Banner not found"}
        # swap order with the adjacent neighbour in the requested direction
        if payload.direction == "up":
            neighbour = await Banners.objects.filter(order__lt=b.order).order_by("-order").afirst()
        else:
            neighbour = await Banners.objects.filter(order__gt=b.order).order_by("order").afirst()
        if neighbour is None:
            return True, {"banners": [_banner_dict(x) for x in await sync_to_async(list)(Banners.objects.all())]}
        b.order, neighbour.order = neighbour.order, b.order
        await sync_to_async(b.save)()
        await sync_to_async(neighbour.save)()
        rows = await sync_to_async(list)(Banners.objects.all())
        return True, {"banners": [_banner_dict(x) for x in rows]}


BANNERS_CONTROLLER = BannersController()
