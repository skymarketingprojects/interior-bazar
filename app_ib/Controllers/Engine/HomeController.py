"""
HomeController — powers the home-page sections that are recommendations / feeds
rather than raw pre-computed boards.

Recommendation heuristic (v1, no ML): start from the pre-computed trendingScore,
boost by city match and by the user's recent search terms. Location-aware where
coordinates exist (shops), city-aware otherwise.
"""
from app_ib.Utils.EngineConfig import ENTITY_TYPE, ALGO, HOME_FILTER
from app_ib.Utils.SafeCache import safe_cache as cache
from app_ib.algorithms.helpers import get_model, haversine_km
from app_ib.algorithms.ranking import nearby_search
from app_ib.algorithms.text import normalize


class _HomeController:

    # ---------------- recommendations (sections 2,3,4,7) ----------------
    def recommend(self, entity_type, user=None, city="", limit=12,
                  filter_code="", category_id=None, lat=None, lng=None,
                  radius_km=None):
        """Personalized feed. `filter_code` / `category_id` come from the home
        filter bar (see home_filters()); with neither set the behavior is
        byte-identical to the original unfiltered recommend().

        Personalization (no filter, logged-in user): the trendingScore baseline
        is boosted by (a) the user's recent search TERMS and (b) the categories
        of the user's recently-VIEWED items. Both are bounded look-backs so the
        feed reflects "what this user is into" without an unbounded query cost.

        Geo restriction: when ANY filter or category is active AND the caller
        sends lat/lng, the feed is post-filtered to businesses within
        `radius_km` (default HOME_FILTER.FORYOU_RADIUS_KM, ~100km) using the
        haversine math from algorithms.ranking. Businesses without coordinates
        fall back to a city match so legacy (un-geocoded) rows aren't silently
        dropped. With NO filter there is NO geo restriction (legacy behavior).
        """
        model = get_model(entity_type)
        qs = model.objects.all()
        if entity_type in (ENTITY_TYPE.PRODUCT, ENTITY_TYPE.SERVICE):
            qs = qs.filter(isActive=True)
        qs = self._apply_home_filter(qs, entity_type, filter_code, category_id,
                                     city=city, lat=lat, lng=lng)
        terms = self._recent_terms(user)
        # Recently-viewed category boost: only when the feed is NOT filtered,
        # i.e. the "show me my usual stuff" home view. When a filter/category is
        # active the user has expressed an explicit intent, so we don't dilute it.
        boost_cats = set()
        if not filter_code and not category_id:
            boost_cats = {cid for cid, _ in self._recent_categories(user)}
        city_l = (city or "").strip().lower()
        # Geo is active only with an explicit filter/category selection + coords.
        geo_active = bool((filter_code or category_id) and lat is not None and lng is not None)
        radius = float(radius_km) if radius_km else HOME_FILTER.FORYOU_RADIUS_KM

        scored = []
        for obj in qs.order_by("-trendingScore")[:200]:
            ecity = self._entity_city(obj, entity_type)
            dist = None
            if geo_active:
                dist = self._entity_distance(obj, entity_type, float(lat), float(lng))
                if dist is not None:
                    if dist > radius:
                        continue  # outside the radius — drop it
                # no coordinates -> keep only when the city matches (documented
                # fallback so un-geocoded businesses still surface in their city)
                elif not (city_l and ecity and ecity.lower() == city_l):
                    continue
            score = (getattr(obj, "trendingScore", 0.0) or 0.0) + 1.0  # +1 so cold items still rank
            if city_l and ecity and ecity.lower() == city_l:
                score *= 1.5
            blob = self._text_blob(obj, entity_type)
            for t in terms:
                if t and t in blob:
                    score += 5.0
            if boost_cats and self._entity_category_ids(obj, entity_type) & boost_cats:
                score += HOME_FILTER.RECENT_VIEW_CATEGORY_BOOST  # shares a category w/ recently-viewed
            scored.append((score, obj, dist))
        scored.sort(key=lambda s: s[0], reverse=True)
        return [self._entity_dict(o, entity_type, round(sc, 3), distance_km=d)
                for sc, o, d in scored[:limit]]

    # ---------------- verified business = architects (section 5) ----------------
    def recommend_architects(self, user=None, city="", limit=12):
        from app_ib.models import Architect
        city_l = (city or "").strip().lower()
        scored = []
        for a in Architect.objects.filter(isActive=True).order_by("-trendingScore")[:200]:
            score = (a.trendingScore or 0.0) + 1.0
            if city_l and a.city and a.city.lower() == city_l:
                score *= 1.5
            scored.append((score, a))
        scored.sort(key=lambda s: s[0], reverse=True)
        return [{"entityType": ENTITY_TYPE.ARCHITECT, "id": a.id, "name": a.name, "slug": a.slug,
                 "city": a.city, "state": a.state, "imageUrl": a.coverImage,
                 "rating": a.rating, "trendingScore": a.trendingScore} for _, a in scored[:limit]]

    # ---------------- shops near you (section 6) ----------------
    def nearby_shops(self, lat, lng, radius_km=None, city="", limit=20):
        from app_ib.models import Shop
        if lat is not None and lng is not None:
            coords = [(s.id, float(s.lat), float(s.lng)) for s in
                      Shop.objects.filter(isActive=True, lat__isnull=False, lng__isnull=False)]
            ranked = nearby_search(float(lat), float(lng), coords, radius_km)  # [(id, dist)]
            shops = {s.id: s for s in Shop.objects.filter(id__in=[i for i, _ in ranked])}
            out = []
            for sid, dist in ranked[:limit]:
                s = shops.get(sid)
                if s:
                    out.append({**self._shop_dict(s), "distanceKm": dist})
            return out
        # no coordinates -> fall back to city match, trending order
        qs = Shop.objects.filter(isActive=True)
        if city:
            qs = qs.filter(city__iexact=city)
        return [self._shop_dict(s) for s in qs.order_by("-trendingScore")[:limit]]

    # ---------------- reels / hot short-videos (section 1) ----------------
    def reels(self, limit=20):
        """'Trending now' reel mix: mostly hotScore-ranked + a few newest uploads.

        WHY the mix: pure hotScore ranking (= most-visited entities) starves
        brand-new videos of exposure (cold start), so a handful of the newest
        ShortVideoLinks (by createdAt) are blended into the hot list at fixed
        slots. Blended items are flagged isNew=True; everything about the
        response is ADDITIVE (slug/isNew added, nothing renamed/removed)
        because the Trending page consumes this same endpoint.
        `slug` is the linked entity's slug so the frontend can deep-link from
        a playing reel straight to the product/service/business detail page.
        """
        from app_ib.models import ShortVideoLink, FallbackVideo
        rows = (ShortVideoLink.objects.select_related("platform", "contentType")
                .order_by("-isPrimary", "displayOrder")[:200])
        candidates = {}   # video pk -> reel dict (dedupes hot vs new picks by video)
        created_at = {}   # video pk -> createdAt (kept out of the API payload)
        for v in rows:
            model = v.contentType.model_class() if v.contentType else None
            obj = model.objects.filter(id=v.objectId).first() if model else None
            if not obj:
                continue
            candidates[v.id] = {
                "videoUrl": v.videoUrl,
                "platform": v.platform.code if v.platform else "",
                "entityType": v.contentType.model, "entityId": obj.id,
                "slug": getattr(obj, "slug", "") or "",
                "name": self._name(obj), "imageUrl": self._image(obj),
                "hotScore": getattr(obj, "hotScore", 0.0) or 0.0,
                "isNew": False,
            }
            created_at[v.id] = v.createdAt
        # ~1 in 5 slots reserved for fresh uploads (at least 2 when reels exist)
        new_slots = max(2, limit // 5) if candidates else 0
        newest_ids = sorted(created_at, key=lambda i: created_at[i], reverse=True)[:new_slots]
        for vid in newest_ids:
            candidates[vid]["isNew"] = True
        hot = sorted((d for vid, d in candidates.items() if vid not in newest_ids),
                     key=lambda d: d["hotScore"], reverse=True)
        out = hot[:max(0, limit - len(newest_ids))]
        # blend the newest in at every-5th positions (2, 7, 12 …) so the row
        # still reads as "trending" while fresh content is visibly mixed in
        for i, vid in enumerate(newest_ids):
            out.insert(min(2 + i * 5, len(out)), candidates[vid])
        out = out[:limit]
        # backfill with developer-seeded fallback videos if short on real reels
        if len(out) < limit:
            for fv in FallbackVideo.objects.filter(isActive=True).order_by("displayOrder")[:limit - len(out)]:
                out.append({"videoUrl": fv.videoUrl, "platform": fv.platform.code if fv.platform else "",
                            "entityType": "", "entityId": None, "slug": "", "name": "", "imageUrl": "",
                            "hotScore": 0.0, "isNew": False, "isFallback": True})
        return out

    # ---------------- video stories = testimonials (section 9) ----------------
    def testimonials(self, limit=12):
        from app_ib.models import Testimonial
        return [{"id": t.id, "videoUrl": t.videoUrl, "thumbnailUrl": t.thumbnailUrl,
                 "authorName": t.authorName, "authorRole": t.authorRole,
                 "businessName": t.businessName, "quote": t.quote, "rating": t.rating}
                for t in Testimonial.objects.filter(isActive=True)[:limit]]

    # ---------------- in their words = random reviews (section 11) ----------------
    def random_reviews(self, limit=10):
        from app_ib.models import Review
        qs = (Review.objects.filter(business__isnull=False, isDeleted=False, isApproved=True)
              .exclude(body="").select_related("business", "reviewer").order_by("?")[:limit])
        out = []
        for r in qs:
            out.append({"reviewId": r.id, "rating": r.rating, "title": r.title, "body": r.body,
                        "businessId": r.business_id,
                        "businessName": r.business.businessName if r.business else "",
                        "timestamp": r.timestamp.isoformat()})
        return out

    # ---------------- home filter bar (GET home/filters/) ----------------
    def home_filters(self, user=None):
        """Pills for the home-page filter row.

        Two kinds (the frontend needs both to build its follow-up request):
          basic    -> {id, kind:'basic', code, label, icon}   (icons: tabler ids)
          category -> {id, kind:'category', categoryId, label} (NO icon by design)

        Category pills are derived from the user's RecentlyViewed rows so the
        bar reflects what the user actually browses; anonymous users (or users
        whose history resolves to nothing) get the platform-popular categories
        instead, so the bar is never empty.
        """
        out = [{"id": f"basic:{code}", "kind": HOME_FILTER.KIND_BASIC,
                "code": code, "label": label, "icon": icon}
               for code, label, icon in HOME_FILTER.BASIC]
        cats = self._recent_categories(user) or self._popular_categories()
        out += [{"id": f"category:{cid}", "kind": HOME_FILTER.KIND_CATEGORY,
                 "categoryId": cid, "label": label} for cid, label in cats]
        return out

    def _recent_categories(self, user):
        """BusinessCategory pills derived from the user's last N viewed items,
        ranked by frequency. Returns [] when nothing resolves (caller falls
        back to _popular_categories). Query cost is bounded: one query for the
        RecentlyViewed page + at most one prefetched query per entity model."""
        if not user or not getattr(user, "is_authenticated", False):
            return []
        from collections import Counter
        from app_ib.engine_models import RecentlyViewed
        rows = (RecentlyViewed.objects.filter(user=user)
                .select_related("contentType")
                .order_by("-viewedAt")[:HOME_FILTER.RECENT_ROWS])
        # bucket object ids per model so each model is hit once (no N+1)
        ids_by_model = {}
        for rv in rows:
            model = rv.contentType.model_class()
            if model is not None:
                ids_by_model.setdefault(model, []).append(rv.objectId)
        from app_ib.models import Business
        counter = Counter()       # categoryId -> view frequency
        labels = {}               # categoryId -> display label
        for model, ids in ids_by_model.items():
            if model is Business:
                objs = model.objects.filter(id__in=ids).prefetch_related("businessCategory")
                biz_of = lambda o: o  # noqa: E731 — trivial accessor
            elif hasattr(model, "business"):
                # Product / Service / Catelogue all carry a direct FK to the
                # owning Business — categories come from that business.
                objs = model.objects.filter(id__in=ids).prefetch_related("business__businessCategory")
                biz_of = lambda o: o.business  # noqa: E731
            else:
                continue  # Shop/Architect etc. have no BusinessCategory link
            for obj in objs:
                biz = biz_of(obj)
                if not biz:
                    continue
                for cat in biz.businessCategory.all():
                    counter[cat.id] += 1
                    labels[cat.id] = cat.lable  # `lable` typo is the real column
        ranked = counter.most_common(HOME_FILTER.MAX_CATEGORY_PILLS)
        return [(cid, labels[cid]) for cid, _ in ranked]

    def _popular_categories(self):
        """Fallback pills: the platform's most famous categories — trending
        flag first, then by how many businesses use them. Cached (SafeCache)
        because this runs on every anonymous home load and the taxonomy is
        near-static."""
        cached = cache.get(HOME_FILTER.POPULAR_CACHE_KEY)
        if cached is not None:
            return cached
        from django.db.models import Count
        from app_ib.models import BusinessCategory
        qs = (BusinessCategory.objects
              .annotate(bizCount=Count("business_category"))
              .order_by("-trending", "-bizCount", "index")[:HOME_FILTER.MAX_CATEGORY_PILLS])
        result = [(c.id, c.lable) for c in qs]
        cache.set(HOME_FILTER.POPULAR_CACHE_KEY, result, HOME_FILTER.POPULAR_CACHE_TTL)
        return result

    def _apply_home_filter(self, qs, entity_type, filter_code, category_id,
                           city="", lat=None, lng=None):
        """Translate a filter-bar selection into queryset constraints.

        Filters are defined on Business; for product/service/catelogue feeds we
        apply them through the owning `business` FK so one code path serves all
        for-you entity types. Unknown codes are ignored (= no filter) so stale
        frontend pills can never 500 the home page.
        """
        prefix = "" if entity_type == ENTITY_TYPE.BUSINESS else "business__"
        if category_id:
            qs = qs.filter(**{f"{prefix}businessCategory__id": category_id}).distinct()
        if filter_code == HOME_FILTER.VERIFIED:
            qs = qs.filter(**{f"{prefix}isVerified": True})
        elif filter_code == HOME_FILTER.TOP_RATED:
            qs = qs.filter(**{f"{prefix}ratingValue__gte": HOME_FILTER.TOP_RATED_MIN})
        elif filter_code == HOME_FILTER.OPEN_NOW:
            qs = qs.filter(self._open_now_q(prefix)).distinct()
        elif filter_code == HOME_FILTER.NEAR_ME:
            # Business now HAS lat/lng (additive fields). When the caller sends
            # coordinates the precise radius restriction is applied later in
            # recommend() (haversine post-filter, shared by every active filter).
            # Only when coordinates are MISSING do we keep the coarse city match
            # so "Near me" still narrows the feed without geolocation.
            if (lat is None or lng is None) and city:
                qs = qs.filter(**{f"{prefix}business_location__city__iexact": city.strip()})
        return qs

    def _open_now_q(self, prefix):
        """Q for 'business is open right now' against DaySchedule rows
        (day 1=Mon..7=Sun, startTime/endTime, isWorking). Handles overnight
        windows (start > end, e.g. 18:00-02:00) by also checking yesterday's
        row after midnight. All conditions live in ONE Q so they bind to the
        same schedule row (chained .filter() calls would join separate rows)."""
        from django.db.models import Q, F
        from django.utils import timezone
        now = timezone.localtime()
        day, t = now.isoweekday(), now.time()
        prev_day = day - 1 or 7
        d, s, e, w = (f"{prefix}schedules__day", f"{prefix}schedules__startTime",
                      f"{prefix}schedules__endTime", f"{prefix}schedules__isWorking")
        today_open = Q(**{d: day, w: True}) & (
            Q(**{f"{s}__lte": t, f"{e}__gte": t}) |                      # normal window
            Q(**{f"{s}__gt": F(e), f"{s}__lte": t}))                     # overnight, before midnight
        yesterday_spill = Q(**{d: prev_day, w: True}) & \
            Q(**{f"{s}__gt": F(e), f"{e}__gte": t})                      # overnight, after midnight
        return today_open | yesterday_spill

    # ---------------- helpers ----------------
    def _recent_terms(self, user):
        if not user or not getattr(user, "is_authenticated", False):
            return []
        from app_ib.models import SearchEvent
        words = set()
        for q in (SearchEvent.objects.filter(user=user).order_by("-timestamp")
                  .values_list("normalizedQuery", flat=True)[:10]):
            for w in normalize(q).split():
                if len(w) >= 4:
                    words.add(w)
        return list(words)

    def _entity_business(self, obj, entity_type):
        """Owning Business for a feed object: the object itself for the business
        feed, else its `business` FK (product/service/catelogue). Architects/
        shops have no Business link, so geo/category boosts simply don't apply."""
        if entity_type == ENTITY_TYPE.BUSINESS:
            return obj
        return getattr(obj, "business", None)

    def _entity_distance(self, obj, entity_type, user_lat, user_lng):
        """Haversine km from (user_lat, user_lng) to the entity's Business
        coordinates, or None when the business has no lat/lng (caller treats
        None as 'fall back to city match'). Reuses the same great-circle math
        as algorithms.ranking.nearby_search (via haversine_km)."""
        biz = self._entity_business(obj, entity_type)
        lat = getattr(biz, "lat", None) if biz else None
        lng = getattr(biz, "lng", None) if biz else None
        if lat is None or lng is None:
            return None
        return round(haversine_km(user_lat, user_lng, float(lat), float(lng)), 3)

    def _entity_category_ids(self, obj, entity_type):
        """Set of BusinessCategory ids for the entity's owning business — used to
        match against the user's recently-viewed categories (the view-history
        boost). Empty set for entities with no business link."""
        biz = self._entity_business(obj, entity_type)
        if not biz:
            return set()
        try:
            return {c.id for c in biz.businessCategory.all()}
        except Exception:
            return set()

    def _entity_city(self, obj, entity_type):
        try:
            if entity_type == ENTITY_TYPE.ARCHITECT:
                return obj.city
            if entity_type == ENTITY_TYPE.SHOP:
                return obj.city
            if entity_type == ENTITY_TYPE.BUSINESS:
                loc = getattr(obj, "business_location", None)
                return loc.city if loc else ""
            biz = getattr(obj, "business", None)
            loc = getattr(biz, "business_location", None) if biz else None
            return loc.city if loc else ""
        except Exception:
            return ""

    def _text_blob(self, obj, entity_type):
        parts = [self._name(obj),
                 getattr(obj, "bio", "") or getattr(obj, "description", "") or ""]
        return normalize(" ".join(parts))

    def _name(self, o):
        return (getattr(o, "businessName", None) or getattr(o, "name", None)
                or getattr(o, "title", None) or "")

    def _image(self, o):
        return (getattr(o, "coverImageUrl", None) or getattr(o, "coverImage", None)
                or getattr(o, "catelougeImage", None) or "")

    def _shop_dict(self, s):
        return {"entityType": ENTITY_TYPE.SHOP, "id": s.id, "name": s.name, "slug": s.slug,
                "city": s.city, "imageUrl": s.coverImage, "shopType": s.shopType,
                "rating": s.rating, "trendingScore": s.trendingScore}

    def _entity_dict(self, o, entity_type, score, distance_km=None):
        """Feed-card payload. The first block of keys is FROZEN (existing
        frontend consumers depend on them); everything after is ADDITIVE
        enrichment so cards can show more without breaking old callers."""
        d = {"entityType": entity_type, "id": o.id, "name": self._name(o),
             "slug": getattr(o, "slug", "") or "", "imageUrl": self._image(o),
             "rating": (getattr(o, "ratingValue", None) if hasattr(o, "ratingValue")
                        else getattr(o, "rating", 0.0)),
             "trendingScore": getattr(o, "trendingScore", 0.0) or 0.0,
             "label": getattr(o, "label", "") or "", "recScore": score}
        # --- additive enrichment (new keys only) ---
        biz = self._entity_business(o, entity_type)
        d["city"] = self._entity_city(o, entity_type) or ""
        d["hotScore"] = getattr(o, "hotScore", 0.0) or 0.0
        d["totalReviews"] = getattr(o, "totalReviews", 0) or 0
        # verified status lives on Business; product/service inherit the owner's
        d["isVerified"] = bool(getattr(biz, "isVerified", False)) if biz else False
        if distance_km is not None:
            d["distanceKm"] = distance_km
        # business-type label (cheap, useful chip) for the business feed
        if entity_type == ENTITY_TYPE.BUSINESS:
            bt = getattr(o, "businessType", None)
            d["businessType"] = getattr(bt, "lable", "") if bt else ""
        # product/service pricing — expose the legacy `displayPrice`/`orignalPrice`
        # (note the baked-in `orignalPrice` column typo) under corrected, frozen
        # public key names so cards can render a price tag.
        if entity_type in (ENTITY_TYPE.PRODUCT, ENTITY_TYPE.SERVICE):
            d["price"] = getattr(o, "displayPrice", None)
            d["originalPrice"] = getattr(o, "orignalPrice", None)
        return d


HOME_CONTROLLER = _HomeController()
