from asgiref.sync import sync_to_async
from typing import Any, Dict, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.models import Blog
from interior_admin.Controllers.Audit.AuditController import append_audit


def _blog(b: Blog) -> Dict[str, Any]:
    return {"id": b.id, "title": b.title, "slug": b.slug, "author": b.author,
            "coverImageUrl": b.coverImageUrl, "isFeatured": b.isFeatured,
            "createdAt": b.timestamp.isoformat() if b.timestamp else ""}


class ContentController:
    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def List(cls, pageNo: int = 1, pageSize: int = 20) -> Tuple[bool, Dict[str, Any]]:
        pageNo = max(1, pageNo or 1); pageSize = min(100, max(1, pageSize or 20))
        start = (pageNo - 1) * pageSize
        qs = Blog.objects.all().order_by("-id")
        total = await qs.acount()
        rows = await sync_to_async(list)(qs[start:start + pageSize])
        return True, {"blogs": [_blog(b) for b in rows], "total": total, "pageNo": pageNo, "pageSize": pageSize}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def ToggleFeatured(cls, blogId: int, actor=None) -> Tuple[bool, Dict[str, Any]]:
        b = await Blog.objects.filter(id=blogId).afirst()
        if b is None:
            return False, {"message": "Blog not found"}
        b.isFeatured = not b.isFeatured
        await sync_to_async(b.save)()
        await append_audit(actor=actor, action=("blog_featured" if b.isFeatured else "blog_unfeatured"),
                           module_key="content", detail=f"blog={b.id}")
        return True, _blog(b)


CONTENT_CONTROLLER = ContentController()
