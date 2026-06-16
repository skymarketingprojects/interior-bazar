"""
HomeBannerController — serves the home-page hero carousel slides from the
HomeHeroBanner tables (interior_advertisement app).

WHY a dedicated controller (instead of growing HomeController): the hero
banner is editorial/promotional content with its own models, its own cache
key and its own backfill rules — isolating it keeps HomeController focused on
recommendation feeds and lets this module evolve (scheduling, A/B slots,
per-city banners) without touching the recommendation code. It also means
parallel work on other home sections never conflicts with this file.

Caching: SafeCache (Redis-tolerant) with a short TTL. Banners are edited via
Django admin and change rarely; a 10-minute warm window keeps admin edits
near-live without wiring invalidation signals. When Redis is down SafeCache
degrades to a miss and we recompute from the DB — the endpoint never 500s
because of the cache backend.
"""
from django.db.models import Prefetch
from django.utils import timezone

from app_ib.Utils.SafeCache import safe_cache as cache

# Slides render exactly this many business cards; assigned businesses win,
# top-trending businesses backfill the rest so cards never render empty.
BUSINESSES_PER_BANNER = 2
CACHE_KEY = "home:hero_banners"  # page='home' key — kept for back-compat (seed import)
CACHE_TTL = 10 * 60  # 10 min — editorial content, near-live admin edits
DEFAULT_PAGE = "home"


def cache_key_for(page):
    """Per-page cache key. 'home' keeps the historical key so existing cache
    invalidation (seed command, future signals) keeps working unchanged."""
    return CACHE_KEY if page == DEFAULT_PAGE else f"banners:{page}"


class _HomeBannerController:

    def hero_banners(self, page=DEFAULT_PAGE):
        """Return a page's active, in-window hero slides as plain dicts.

        `page` selects which page's banners to serve (home/architects/shops/…);
        any page with no rows returns [] and the frontend keeps its static
        fallback. Response item shape (consumed by the v3 hero adapters):
        { id, tag, title, description,
          background: {gradient, imageUrl},
          buttons:    [{label, link, isPrimary}],        # 0–2, primary first
          metrics:    [{metric, description, index}],    # sorted by index
          businesses: [2 × {id, name, slug, imageUrl, rating, city}] }
        """
        page = page or DEFAULT_PAGE
        key = cache_key_for(page)
        cached = cache.get(key)
        if cached is not None:
            return cached

        from interior_advertisement.models import HomeHeroBanner, BannerButton, BannerMetric

        now = timezone.now()
        qs = (HomeHeroBanner.objects.filter(isActive=True, page=page)
              # NULL window bounds mean "evergreen" — only exclude when a bound exists and is violated
              .exclude(startsAt__isnull=False, startsAt__gt=now)
              .exclude(endsAt__isnull=False, endsAt__lt=now)
              .order_by("displayOrder", "id")
              .prefetch_related(
                  Prefetch("buttons", queryset=BannerButton.objects.order_by("-isPrimary", "id")),
                  Prefetch("metrics", queryset=BannerMetric.objects.order_by("index", "id")),
                  "businesses__business_location",
              ))

        banners = list(qs)
        backfill = self._backfill_pool(banners)

        data = [self._banner_dict(b, backfill) for b in banners]
        cache.set(key, data, CACHE_TTL)
        return data

    # ---------------- internals ----------------

    def _backfill_pool(self, banners):
        """Top-trending businesses used to fill slides that have fewer than
        BUSINESSES_PER_BANNER assigned. Fetched once per request (not per
        banner) so the endpoint stays O(1) queries regardless of slide count."""
        from app_ib.models import Business
        pool_size = max(len(banners), 1) * BUSINESSES_PER_BANNER
        return list(Business.objects.select_related("business_location")
                    .order_by("-trendingScore", "id")[:pool_size])

    def _banner_dict(self, banner, backfill):
        businesses = list(banner.businesses.all()[:BUSINESSES_PER_BANNER])
        if len(businesses) < BUSINESSES_PER_BANNER:
            have = {b.id for b in businesses}
            for biz in backfill:
                if len(businesses) >= BUSINESSES_PER_BANNER:
                    break
                if biz.id not in have:
                    businesses.append(biz)
                    have.add(biz.id)

        return {
            "id": banner.id,
            "tag": banner.tag,
            "title": banner.title,
            "description": banner.description,
            "background": {
                "gradient": banner.backgroundGradient,
                "imageUrl": banner.backgroundImageUrl,
            },
            "buttons": [{"label": b.label, "link": b.link, "isPrimary": b.isPrimary}
                        for b in banner.buttons.all()],
            "metrics": [{"metric": m.metric, "description": m.description, "index": m.index}
                        for m in banner.metrics.all()],
            "businesses": [self._business_dict(b) for b in businesses],
        }

    def _business_dict(self, biz):
        """Small-card projection of a Business. Rating prefers the engine's
        float `ratingValue`; falls back to the legacy `rating` CharField so
        pre-engine rows still show something sensible."""
        loc = getattr(biz, "business_location", None)
        rating = biz.ratingValue or 0.0
        if not rating:
            try:
                rating = float(biz.rating or 0.0)
            except (TypeError, ValueError):
                rating = 0.0
        return {
            "id": biz.id,
            "name": biz.businessName,
            "slug": biz.slug or "",
            "imageUrl": biz.coverImageUrl or "",
            "rating": round(rating, 1),
            "city": loc.city if loc else "",
        }


HOME_BANNER_CONTROLLER = _HomeBannerController()
