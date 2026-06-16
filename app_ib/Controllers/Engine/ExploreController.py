"""
ExploreController — Explore page sections.
  - search_cards()   reuse trending searches (cards redirect to home + add filter)
  - editors_pick()   trending architect(s) + AI editorial copy (pre-computed)
  - design_ideas()   architect projects feed (any architect)
"""
from django.utils import timezone

from app_ib.Controllers.Engine.CrudController import NotFound_


class _ExploreController:

    # ---- Editors Pick (1) ----
    def editors_pick(self, limit=5):
        from app_ib.models import EditorsPick, Architect
        today = timezone.now().date()
        qs = EditorsPick.objects.filter(isPublished=True)
        latest = qs.filter(snapshotDate=today)
        rows = (latest if latest.exists() else qs).order_by("rank")[:limit]
        archs = {a.id: a for a in Architect.objects.filter(id__in=[r.architect_id for r in rows])}
        out = []
        for r in rows:
            a = archs.get(r.architect_id)
            out.append({
                "architectId": r.architect_id,
                "name": a.name if a else "", "slug": a.slug if a else "",
                "city": a.city if a else "", "state": a.state if a else "",
                "rating": a.rating if a else 0.0,
                "eyebrow": r.eyebrow, "headline": r.headline, "body": r.body,
                "trendTags": r.trendTags, "imageUrl": r.imageUrl, "rank": r.rank,
            })
        return out

    # ---- Design Ideas (2) ----
    def design_ideas(self, architect_id=None, style="", city="", limit=30):
        from app_ib.models import Project
        qs = Project.objects.filter(isActive=True).select_related("architect")
        if architect_id:
            qs = qs.filter(architect_id=architect_id)
        if style:
            qs = qs.filter(style__iexact=style)
        if city:
            qs = qs.filter(city__iexact=city)
        out = []
        for p in qs[:limit]:
            out.append({
                "projectId": p.id, "title": p.title, "slug": p.slug,
                "description": p.description, "coverImage": p.coverImage,
                "images": p.images, "city": p.city, "style": p.style, "tags": p.tags,
                "architectId": p.architect_id,
                "architectName": p.architect.name if p.architect else "",
                "viewCount": p.viewCount,
            })
        return out

    # ---- search cards (reuse trending searches) ----
    def search_cards(self):
        from app_ib.Controllers.Engine.EngineController import ENGINE_CONTROLLER
        return ENGINE_CONTROLLER.trending_searches(category_fallback=True)


ENGINE_EXPLORE_CONTROLLER = _ExploreController()


# ---- write: architect adds a project (design idea) ----
def create_project(user, architect_id, payload):
    from app_ib.models import Architect, Project
    from app_ib.Controllers.Engine.CrudController import PermissionError_
    arch = Architect.objects.filter(id=architect_id).first()
    if not arch:
        raise NotFound_("architect not found")
    if arch.user_id != user.id:
        raise PermissionError_("not the architect owner")
    p = Project.objects.create(
        architect=arch, title=payload.get("title", "").strip() or "Untitled Project",
        description=payload.get("description", ""), coverImage=payload.get("coverImage", ""),
        images=payload.get("images", []), city=payload.get("city", arch.city),
        state=payload.get("state", arch.state), style=payload.get("style", ""),
        tags=payload.get("tags", []))
    return {"projectId": p.id, "slug": p.slug, "title": p.title}
