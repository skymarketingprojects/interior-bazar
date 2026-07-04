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
    def recommend(self, entity_type, user=None, city="", state="", limit=12,
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
        state_l = (state or "").strip().lower()
        # Geo is active only with an explicit filter/category selection + coords.
        geo_active = bool((filter_code or category_id) and lat is not None and lng is not None)
        radius = float(radius_km) if radius_km else HOME_FILTER.FORYOU_RADIUS_KM
        top = list(qs.order_by("-trendingScore")[:200])

        def _pass(apply_geo):
            out = []
            for obj in top:
                ecity = self._entity_city(obj, entity_type)
                dist = None
                if apply_geo:
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
                elif state_l:  # same-state (not same-city) gets a smaller nudge
                    est = self._entity_state(obj, entity_type)
                    if est and est.lower() == state_l:
                        score *= 1.2
                blob = self._text_blob(obj, entity_type)
                for t in terms:
                    if t and t in blob:
                        score += 5.0
                if boost_cats and self._entity_category_ids(obj, entity_type) & boost_cats:
                    score += HOME_FILTER.RECENT_VIEW_CATEGORY_BOOST  # shares a category w/ recently-viewed
                out.append((score, obj, dist))
            return out

        scored = _pass(geo_active)
        # Broaden so a section is never empty: if the radius/city geo gate removed
        # everything, re-rank the same trending pool without the geo restriction
        # (city/state stay as score boosts). The unfiltered path already returns
        # all-trending, so it only empties when the entity table itself is empty.
        if not scored and geo_active:
            scored = _pass(False)
        scored.sort(key=lambda s: s[0], reverse=True)
        return [self._entity_dict(o, entity_type, round(sc, 3), distance_km=d)
                for sc, o, d in scored[:limit]]

    # ---------------- verified business = architects (section 5) ----------------
    def recommend_architects(self, user=None, city="", state="", limit=12):
        from app_ib.models import Architect
        city_l = (city or "").strip().lower()
        state_l = (state or "").strip().lower()
        scored = []
        # Ranks the whole active pool (city/state are score boosts, not filters),
        # so it is never empty unless there are no active architects at all.
        for a in Architect.objects.filter(isActive=True).order_by("-trendingScore")[:200]:
            score = (a.trendingScore or 0.0) + 1.0
            if city_l and a.city and a.city.lower() == city_l:
                score *= 1.5
            elif state_l and a.state and a.state.lower() == state_l:
                score *= 1.2
            scored.append((score, a))
        scored.sort(key=lambda s: s[0], reverse=True)
        return [{"entityType": ENTITY_TYPE.ARCHITECT, "id": a.id, "name": a.name, "slug": a.slug,
                 "city": a.city, "state": a.state, "imageUrl": a.coverImage,
                 "rating": a.rating, "trendingScore": a.trendingScore} for _, a in scored[:limit]]

    # ---------------- verified businesses (section 5, reworked) ----------------
    def verified_businesses(self, user=None, city="", state="", limit=12):
        """Rank the home 'Verified businesses' section by ONE verified-business
        score combining six signals, each normalised to 0..1 ACROSS THE CANDIDATE
        POOL so nothing needs a hardcoded threshold:

          proximity   same city (1.0) > same state (0.6) > elsewhere (0.2)
          age         older-than-peers, ranked by creation date within the pool
          completed   count of 'won' (completed/green) project leads, log-damped
          conversion  won / total leads — the lead-status green/completed ratio
          response    faster avg first-response ranks higher (inverse, relative)
          rating      ratingValue / 5

        Verified businesses are strongly preferred; the pool broadens to all
        active businesses only when too few verified ones exist, so the section
        is never empty (returns [] only when there are no active businesses).
        """
        import math
        from django.db.models import Count, Q as DQ
        from django.utils import timezone
        from app_ib.models import Business, LeadQuery

        base = (Business.objects.filter(isActive=True)
                .select_related("business_location", "business_location__locationState", "businessType"))
        verified = list(base.filter(isVerified=True).order_by("-ratingValue", "-leadCount")[:200])
        pool = verified if len(verified) >= limit else list(
            base.order_by("-isVerified", "-ratingValue", "-leadCount")[:200])
        if not pool:
            return []

        ids = [b.id for b in pool]
        # lead stats in ONE query: total + 'won' (completed/green) leads per business
        stats = {r["business_id"]: r for r in (
            LeadQuery.objects.filter(business_id__in=ids)
            .values("business_id")
            .annotate(total=Count("id"), won=Count("id", filter=DQ(stage="won"))))}

        now = timezone.now()
        ages = {b.id: (now - b.timestamp).total_seconds() for b in pool}
        min_age = min(ages.values())
        age_span = (max(ages.values()) - min_age) or 1.0
        max_won = max((stats.get(b.id, {}).get("won", 0) or 0) for b in pool) or 1
        rts = [b.avgResponseSeconds for b in pool if b.avgResponseSeconds is not None]
        min_rt = min(rts) if rts else 0
        rt_span = ((max(rts) - min_rt) if rts else 0) or 1.0

        city_l, state_l = (city or "").strip().lower(), (state or "").strip().lower()
        # weights sum to 1.0; verified gets a small extra nudge below
        W_PROX, W_AGE, W_DONE, W_CONV, W_RESP, W_RATE = 0.25, 0.10, 0.15, 0.20, 0.10, 0.20

        scored = []
        for b in pool:
            loc = getattr(b, "business_location", None)
            bcity = ((loc.city if loc else "") or "").lower()
            bstate = ((loc.locationState.name if loc and loc.locationState else "") or "").lower()
            if city_l and bcity == city_l:
                prox = 1.0
            elif state_l and bstate == state_l:
                prox = 0.6
            else:
                prox = 0.2
            age = (ages[b.id] - min_age) / age_span
            st = stats.get(b.id, {})
            won, total = st.get("won", 0) or 0, st.get("total", 0) or 0
            completed = math.log1p(won) / math.log1p(max_won)
            conversion = (won / total) if total else 0.0
            if b.avgResponseSeconds is not None and rts:
                response = 1.0 - (b.avgResponseSeconds - min_rt) / rt_span  # faster -> higher
            else:
                response = 0.4  # unknown response time -> slightly below neutral
            rating = min(1.0, (b.ratingValue or 0.0) / 5.0)
            score = (W_PROX * prox + W_AGE * age + W_DONE * completed
                     + W_CONV * conversion + W_RESP * response + W_RATE * rating)
            if b.isVerified:
                score += 0.05  # a verified peer edges out an equal unverified one
            scored.append((score, b, won))
        scored.sort(key=lambda s: s[0], reverse=True)
        out = []
        for sc, b, won in scored[:limit]:
            d = self._entity_dict(b, ENTITY_TYPE.BUSINESS, round(sc, 4))
            d["verifiedScore"] = round(sc, 4)
            d["completedLeads"] = won
            out.append(d)
        return out

    # ---------------- shops near you (section 6) ----------------
    def nearby_shops(self, lat, lng, radius_km=None, city="", state="", limit=20):
        """Shops-near-you, guaranteed non-empty via a broaden chain:
        precise radius (coords) -> same city -> same state -> all shops (trending).
        Each rung is tried only until one yields shops; the section is empty only
        when there are no active shops at all."""
        from app_ib.models import Shop
        base = Shop.objects.filter(isActive=True)
        if lat is not None and lng is not None:
            coords = [(s.id, float(s.lat), float(s.lng)) for s in
                      base.filter(lat__isnull=False, lng__isnull=False)]
            ranked = nearby_search(float(lat), float(lng), coords, radius_km)  # [(id, dist)]
            if ranked:
                shops = {s.id: s for s in base.filter(id__in=[i for i, _ in ranked])}
                out = []
                for sid, dist in ranked[:limit]:
                    s = shops.get(sid)
                    if s:
                        out.append({**self._shop_dict(s), "distanceKm": dist})
                if out:
                    return out
        # no/insufficient coordinate matches -> broaden city -> state -> all
        for scope in self._broaden_shops(base, city, state):
            rows = list(scope.order_by("-trendingScore")[:limit])
            if rows:
                return [self._shop_dict(s) for s in rows]
        return []

    def _broaden_shops(self, base, city, state):
        city = (city or "").strip()
        state = (state or "").strip()
        if city:
            yield base.filter(city__iexact=city)
        if state:
            yield base.filter(state__iexact=state)
        yield base  # country / all — the last rung so the section is never empty

    # ---------------- join us (final CTA band) ----------------
    def join_us(self):
        """The home 'Join us' final CTA band + its ordered process steps. Returns
        {} when none is configured (frontend keeps its static fallback)."""
        from app_ib.engine_models import JoinUsCta
        cta = (JoinUsCta.objects.filter(isActive=True)
               .prefetch_related("steps").order_by("index", "id").first())
        if not cta:
            return {}
        return {
            "eyebrow": cta.eyebrow, "titleLead": cta.titleLead, "titleAccent": cta.titleAccent,
            "sub": cta.sub,
            "primary": {"label": cta.primaryLabel, "action": cta.primaryAction or {}},
            "secondary": {"label": cta.secondaryLabel, "action": cta.secondaryAction or {}},
            "trustBadges": list(cta.trustBadges or []),
            "cardHead": cta.cardHead, "responseNote": cta.responseNote,
            "steps": [{"num": s.key, "text": s.value} for s in cta.steps.all()],
        }

    # ---------------- what makes IB different (differentiator cards) ----------------
    def differentiators(self, limit=12):
        """'What makes IB different' cards — admin-managed icon/heading/description
        + a variable-length `eliminates` list (competing tools IB replaces)."""
        from app_ib.engine_models import Differentiator
        return [{"id": d.id, "icon": d.icon, "iconBg": d.iconBg, "iconColor": d.iconColor,
                 "heading": d.heading, "description": d.description,
                 "eliminates": list(d.eliminates or [])}
                for d in Differentiator.objects.filter(isActive=True).order_by("index", "id")[:limit]]

    # ---------------- get inspired (popular products/services gallery) ----------------
    def get_inspired(self, limit=12):
        """'Get inspired' photo gallery: the most-popular products & services —
        ranked by save count (primary) then trendingScore — each with a real
        image, its save count, rating and owning business. Only items WITH an
        image are returned (it's a gallery); falls back to image-less popular
        items only if nothing has an image, so the section is never empty."""
        from django.contrib.contenttypes.models import ContentType
        from django.db.models import Count
        from app_ib.engine_models import SavedItem
        from interior_products.models import Product, Service

        def _imgs(o, rel):
            # all image URLs of the product/service (ProductImage/ServiceImage.image),
            # ordered by index; the lightbox scrolls through them.
            return [im.image for im in sorted(getattr(o, rel).all(), key=lambda x: x.index) if im.image]

        with_img, without_img = [], []
        for model, et, rel in ((Product, ENTITY_TYPE.PRODUCT, "productImages"),
                               (Service, ENTITY_TYPE.SERVICE, "serviceImages")):
            ct = ContentType.objects.get_for_model(model)
            saves = {r["objectId"]: r["n"] for r in (
                SavedItem.objects.filter(contentType=ct)
                .values("objectId").annotate(n=Count("id")))}
            for o in (model.objects.filter(isActive=True)
                      .select_related("business").prefetch_related(rel)
                      .order_by("-trendingScore")[:100]):
                biz = getattr(o, "business", None)
                sc = saves.get(o.id, 0)
                images = _imgs(o, rel)
                card = {
                    "entityType": et, "id": o.id, "title": o.title, "slug": o.slug or "",
                    "imageUrl": images[0] if images else "",
                    "images": images,  # full set for the fullscreen lightbox gallery
                    "saveCount": sc,
                    "rating": getattr(o, "ratingValue", 0.0) or 0.0,
                    "business": biz.businessName if biz else "",
                    "businessId": biz.id if biz else None,
                    "businessSlug": (biz.slug if biz else "") or "",  # lightbox business nav
                    "_pop": sc * 10 + (getattr(o, "trendingScore", 0.0) or 0.0),
                }
                (with_img if card["imageUrl"] else without_img).append(card)
        pool = with_img or without_img  # gallery prefers images; never empty otherwise
        pool.sort(key=lambda x: x["_pop"], reverse=True)
        return [{k: v for k, v in c.items() if k != "_pop"} for c in pool[:limit]]

    # ---------------- fresh catalogues (Fresh from manufacturers) ----------------
    def fresh_catalogues(self, limit=12):
        """'Fresh from manufacturers' — the newest catalogues, computed once daily
        by cron and cached 24h. On a cold cache the recompute is offloaded to the
        background runner (never blocks the request) and a best-effort live query
        is served so the section is never empty. The request itself NEVER writes
        the cache — only a real daily cron run or the empty-triggered background
        run may (re)create it (see task 33 cache rule)."""
        from app_ib.algorithms.aggregation import (
            FRESH_CATALOGUES_KEY, compute_fresh_catalogues, fresh_catalogues_query)
        cached = cache.get(FRESH_CATALOGUES_KEY)
        if cached:  # warm, non-empty cache -> serve as-is (24h TTL untouched)
            return cached
        # Empty data (cold cache OR a cached empty list): trigger the cron as a
        # BACKGROUND task and serve a best-effort non-empty fallback. The request
        # NEVER writes the cache, so it can't override the daily cron's TTL — only
        # compute_fresh_catalogues (a real cron run or this empty-triggered bg run)
        # (re)creates the cache.
        from app_ib.algorithms.background import enqueue
        enqueue("compute_fresh_catalogues", compute_fresh_catalogues, limit)
        return fresh_catalogues_query(limit)

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
            et = v.contentType.model
            biz = self._entity_business(obj, et)
            candidates[v.id] = {
                "videoUrl": v.videoUrl,
                "platform": v.platform.code if v.platform else "",
                "entityType": et, "entityId": obj.id,
                "slug": getattr(obj, "slug", "") or "",
                "name": self._name(obj), "imageUrl": self._image(obj),
                "hotScore": getattr(obj, "hotScore", 0.0) or 0.0,
                "isNew": False,
                # --- additive FEATURED-SHORT panel enrichment (consumed by the
                # frontend ReelModal; all keys optional so old callers are safe) ---
                "business": self._name(biz) if biz else "",
                "businessId": biz.id if biz else None,
                "city": self._entity_city(obj, et) or "",
                "verified": bool(getattr(biz, "isVerified", False)) if biz else False,
                "description": _clean_desc(getattr(obj, "description", "") or getattr(obj, "bio", "") or ""),
                "rating": (getattr(obj, "ratingValue", None) if hasattr(obj, "ratingValue")
                           else getattr(obj, "rating", None)),
                "reviewCount": getattr(obj, "totalReviews", 0) or 0,
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
        # Serial number (1-based rank as shown in the "Trending now" corner) and a
        # thumbnail derived from the YouTube/Facebook link (falls back to the
        # entity image). Added after final ordering so the serial matches display.
        for i, r in enumerate(out):
            r["serial"] = i + 1
            r["thumbnail"] = _video_thumbnail(r.get("videoUrl", ""), r.get("platform", ""),
                                              r.get("imageUrl", ""))
        # "Top review" panel block — one owning-business review per reel (1 query).
        self._attach_review_quotes(out)
        return out

    def _attach_review_quotes(self, reels):
        """Attach the most recent approved review of each reel's owning business
        as `reviewQuote` (the ReelModal 'Top review' block). One bounded query for
        all businesses in the batch; reels with no business (shops/architects/
        fallbacks) get an empty quote."""
        biz_ids = {r.get("businessId") for r in reels if r.get("businessId")}
        quotes = {}
        if biz_ids:
            from app_ib.models import Review
            for rv in (Review.objects.filter(business_id__in=biz_ids, isApproved=True, isDeleted=False)
                       .exclude(body="").order_by("business_id", "-timestamp")
                       .values("business_id", "body")):
                quotes.setdefault(rv["business_id"], rv["body"])
        for r in reels:
            r["reviewQuote"] = quotes.get(r.get("businessId"), "")

    # ---------------- video stories = testimonials (section 9) ----------------
    def testimonials(self, limit=12):
        from app_ib.models import Testimonial
        return [{"id": t.id, "videoUrl": t.videoUrl, "thumbnailUrl": t.thumbnailUrl,
                 "authorName": t.authorName, "authorRole": t.authorRole,
                 "businessName": t.businessName, "quote": t.quote, "rating": t.rating}
                for t in Testimonial.objects.filter(isActive=True)[:limit]]

    # ---------------- in their words = random reviews (section 11) ----------------
    def random_reviews(self, limit=10):
        """'In their words' — random text testimonials from listed businesses,
        HIGH RATING + positive sentiment only (rating >= 4; there is no separate
        sentiment field, so a high star rating is the positive-sentiment proxy).
        Text only (non-empty body). Distinct from the video-stories section, which
        is served by home/testimonials/ (admin video+text testimonials)."""
        from app_ib.models import Review
        qs = (Review.objects.filter(business__isnull=False, isDeleted=False,
                                    isApproved=True, rating__gte=4)
              .exclude(body="")
              .select_related("business", "reviewer", "business__business_location",
                              "business__businessType")
              .order_by("?")[:limit])
        out = []
        for r in qs:
            biz = r.business
            loc = getattr(biz, "business_location", None) if biz else None
            bt = getattr(biz, "businessType", None) if biz else None
            out.append({"reviewId": r.id, "rating": r.rating, "title": r.title, "body": r.body,
                        "businessId": r.business_id,
                        "businessName": biz.businessName if biz else "",
                        "city": (loc.city if loc else "") or "",              # location line
                        "category": (getattr(bt, "lable", "") or "") if bt else "",  # wt-type category
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

    def _entity_state(self, obj, entity_type):
        """State name for the same-state broaden nudge. Architect/Shop carry a
        plain `state` string; business/product/service resolve it through the
        owning business's Location.locationState FK. Empty on any miss."""
        try:
            if entity_type in (ENTITY_TYPE.ARCHITECT, ENTITY_TYPE.SHOP):
                return getattr(obj, "state", "") or ""
            biz = obj if entity_type == ENTITY_TYPE.BUSINESS else getattr(obj, "business", None)
            loc = getattr(biz, "business_location", None) if biz else None
            st = getattr(loc, "locationState", None) if loc else None
            return st.name if st else ""
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
        url = (getattr(o, "coverImageUrl", None) or getattr(o, "coverImage", None)
               or getattr(o, "catelougeImage", None) or "")
        if url:
            return url
        # Product/Service carry images on related rows, not a cover field —
        # fall back to the first related image (same as EngineController).
        for rel in ("productImages", "serviceImages", "catelogueImages"):
            mgr = getattr(o, rel, None)
            if mgr is not None:
                try:
                    first = list(mgr.all()[:1])
                    if first:
                        return first[0].image
                except Exception:
                    pass
        return ""

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


def _video_thumbnail(video_url, platform, fallback=""):
    """Best-effort still image for a reel derived from its video link:
    YouTube -> i.ytimg.com/vi/<id>/hqdefault.jpg (works for watch/youtu.be/shorts/
    embed URLs). Facebook exposes no public thumbnail URL scheme, so those (and
    anything unrecognised) fall back to the entity's own image."""
    import re
    if not video_url:
        return fallback
    if platform == "youtube" or "youtu" in video_url:
        m = re.search(r"(?:v=|youtu\.be/|shorts/|embed/|/vi/)([\w-]{11})", video_url)
        if m:
            return f"https://i.ytimg.com/vi/{m.group(1)}/hqdefault.jpg"
    return fallback


def _clean_desc(text, limit=220):
    """Plain-text, length-capped description for the reel panel — product/service
    descriptions are rich-text HTML (quill), so strip tags + collapse whitespace."""
    from django.utils.html import strip_tags
    t = " ".join(strip_tags(text or "").split()).strip()
    return (t[:limit].rstrip() + "…") if len(t) > limit else t


HOME_CONTROLLER = _HomeController()
