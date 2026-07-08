import json
from asgiref.sync import sync_to_async
from typing import Any, Dict, Tuple

from django.core.cache import cache

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.models import Blog
from interior_admin.Controllers.Audit.AuditController import append_audit
from .Validators.ContentValidators import BlogCreateSchema, BlogUpdateSchema


def _blog(b: Blog) -> Dict[str, Any]:
    try:
        body = b.description.html if b.description else ""
    except Exception:
        body = ""
    return {"id": b.id, "title": b.title, "slug": b.slug, "author": b.author,
            "coverImageUrl": b.coverImageUrl, "authorImageUrl": b.authorImageUrl,
            "isFeatured": b.isFeatured, "featuredOrder": b.featuredOrder,
            "status": b.status, "body": body,
            "metaTitle": b.metaTitle, "metaDescription": b.metaDescription,
            "focusKeyword": b.focusKeyword,
            "createdAt": b.timestamp.isoformat() if b.timestamp else "",
            "updatedAt": b.updatedAt.isoformat() if b.updatedAt else ""}


def _quill(body_html: str) -> str:
    # django_quill's QuillField expects a JSON string carrying both `delta` and
    # `html` keys. The admin editor only produces HTML, so delta is left empty —
    # the public side only reads `.html` anyway.
    return json.dumps({"delta": "", "html": body_html or ""})


def _bust_blog_caches():
    # BlogsController caches the public list under these keys (1h TTL). Bust them
    # on every write or edits lag up to an hour.
    try:
        cache.delete("all_blogs_list")
    except Exception:
        pass
    try:
        cache.delete_pattern("blogs_pagination_*")  # django-redis only
    except Exception:
        # LocMemCache (dev/SQLite mode) has no delete_pattern — safe to ignore.
        pass


class ContentController:
    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def List(cls, pageNo: int = 1, pageSize: int = 20) -> Tuple[bool, Dict[str, Any]]:
        pageNo = max(1, pageNo or 1); pageSize = min(100, max(1, pageSize or 20))
        start = (pageNo - 1) * pageSize
        # Admin sees ALL blogs (drafts included) — status filtering is public-only.
        qs = Blog.objects.all().order_by("-id")
        total = await qs.acount()
        rows = await sync_to_async(list)(qs[start:start + pageSize])
        return True, {"blogs": [_blog(b) for b in rows], "total": total, "pageNo": pageNo, "pageSize": pageSize}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Create(cls, payload: BlogCreateSchema, actor=None) -> Tuple[bool, Dict[str, Any]]:
        b = Blog(
            title=payload.title, author=payload.author or "",
            coverImageUrl=payload.coverImageUrl or "", authorImageUrl=payload.authorImageUrl or "",
            metaTitle=payload.metaTitle or "", metaDescription=payload.metaDescription or "",
            focusKeyword=payload.focusKeyword or "", status=payload.status or "draft",
            featuredOrder=payload.featuredOrder or 0, isFeatured=bool(payload.isFeatured),
            description=_quill(payload.body or ""),
        )
        if payload.slug:
            b.slug = payload.slug
        await sync_to_async(b.save)()  # save() auto-fills slug from title if empty
        _bust_blog_caches()
        await append_audit(actor=actor, action="blog_created", module_key="content", detail=f"blog={b.id}")
        return True, _blog(b)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Update(cls, blogId: int, payload: BlogUpdateSchema, actor=None) -> Tuple[bool, Dict[str, Any]]:
        b = await Blog.objects.filter(id=blogId).afirst()
        if b is None:
            return False, {"message": "Blog not found"}
        for f in ("title", "author", "slug", "coverImageUrl", "authorImageUrl",
                  "metaTitle", "metaDescription", "focusKeyword", "status",
                  "featuredOrder", "isFeatured"):
            val = getattr(payload, f)
            if val is not None:
                setattr(b, f, val)
        if payload.body is not None:
            b.description = _quill(payload.body)
        await sync_to_async(b.save)()
        _bust_blog_caches()
        await append_audit(actor=actor, action="blog_updated", module_key="content", detail=f"blog={b.id}")
        return True, _blog(b)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Delete(cls, blogId: int, actor=None) -> Tuple[bool, Dict[str, Any]]:
        b = await Blog.objects.filter(id=blogId).afirst()
        if b is None:
            return False, {"message": "Blog not found"}
        await sync_to_async(b.delete)()
        _bust_blog_caches()
        await append_audit(actor=actor, action="blog_deleted", module_key="content", detail=f"blog={blogId}")
        return True, {"id": blogId, "deleted": True}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def ToggleFeatured(cls, blogId: int, actor=None) -> Tuple[bool, Dict[str, Any]]:
        b = await Blog.objects.filter(id=blogId).afirst()
        if b is None:
            return False, {"message": "Blog not found"}
        b.isFeatured = not b.isFeatured
        await sync_to_async(b.save)()
        _bust_blog_caches()
        await append_audit(actor=actor, action=("blog_featured" if b.isFeatured else "blog_unfeatured"),
                           module_key="content", detail=f"blog={b.id}")
        return True, _blog(b)


CONTENT_CONTROLLER = ContentController()
