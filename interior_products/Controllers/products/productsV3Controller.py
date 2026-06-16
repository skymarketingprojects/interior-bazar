"""
v3 product-detail data layer — Redis-free reads for the /v3/products/:slug page.

Deliberately separate from PRODUCTS_CONTROLLER: the legacy controller (and the
endpoints it powers) is frozen for the old frontend and depends on the Redis
cache. These reads go straight to the ORM, so the v3 detail page works with or
without a cache backend. Serves the v3-only views in interior_products/v3Views.py.
"""
import json

from django.db.models import Q

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from interior_products.models import Product

# Human labels for the ProductSpecification titles the legacy product form
# creates (sizeAvailabe/userManual/detail); unknown titles fall back to a
# cleaned-up version of the raw title.
_SPEC_LABELS = {
    'sizeAvailabe': 'Size available',
    'userManual': 'User manual',
    'detail': 'Details',
}

# Rail size bounds for related / from-business lists
_DEFAULT_LIMIT = 10
_MAX_LIMIT = 24


def _not_found() -> LocalResponse:
    return LocalResponse(
        response=RESPONSE_MESSAGES.error,
        message=RESPONSE_MESSAGES.product_fetch_error,
        code=RESPONSE_CODES.not_exist,
        data={'error': RESPONSE_MESSAGES.product_fetch_error},
    )


def _ok(data) -> LocalResponse:
    return LocalResponse(
        response=RESPONSE_MESSAGES.success,
        message=RESPONSE_MESSAGES.product_fetch_success,
        code=RESPONSE_CODES.success,
        data=data,
    )


class PRODUCTS_V3_CONTROLLER:

    # ── builders ──

    @staticmethod
    def _tags(product: Product) -> list:
        try:
            raw = json.loads(str(product.productTags).replace("'", '"')) if product.productTags else []
            return [str(t) for t in raw] if isinstance(raw, list) else []
        except Exception:
            return []

    @staticmethod
    def _images(product: Product) -> list:
        return [
            {'id': im.id, 'imageUrl': im.image, 'index': im.index, 'link': im.link}
            for im in product.productImages.all().order_by('index')
        ]

    @classmethod
    def _card(cls, product: Product) -> dict:
        """Compact card shape for the related / same-business rails."""
        business = product.business
        first_cat = product.category.all().first()
        first_image = product.productImages.all().order_by('index').first()
        return {
            'id': product.id,
            'slug': product.slug,
            'title': product.title,
            'displayPrice': product.displayPrice,
            'originalPrice': product.orignalPrice,
            'categoryName': first_cat.lable if first_cat else '',
            'businessName': business.businessName if business else '',
            'businessSlug': business.slug if business else '',
            'isVerified': bool(business.isVerified) if business else False,
            'ratingValue': product.ratingValue,
            'totalReviews': product.totalReviews,
            'imageUrl': first_image.image if first_image else '',
            'label': product.label or '',
            'inStock': product.stockQuantity is None or product.stockQuantity > 0,
        }

    @staticmethod
    def _rail_queryset(qs):
        return (qs.select_related('business')
                  .prefetch_related('category', 'productImages')
                  .order_by('-trendingScore', '-id'))

    # ── reads ──

    @classmethod
    def getProductDetailV3(cls, slugOrId: str) -> LocalResponse:
        """Full detail payload for one product, looked up by slug or numeric id."""
        qs = Product.objects.select_related(
            'business',
            'business__businessType',
            'business__business_location',
            'business__business_location__locationState',
            'business__business_profile',
            'business__user',
            'business__user__user_profile',
        ).prefetch_related('productImages', 'category', 'subCategory', 'productSpecifications')

        value = str(slugOrId)
        product = qs.filter(id=int(value)).first() if value.isdigit() else qs.filter(slug=value).first()
        if not product:
            return _not_found()

        business = product.business
        location = getattr(business, 'business_location', None) if business else None
        profile = getattr(business, 'business_profile', None) if business else None
        user_profile = None
        if business and business.user_id:
            user_profile = getattr(business.user, 'user_profile', None)

        specifications = [
            {'label': _SPEC_LABELS.get(s.title, str(s.title).replace('_', ' ').capitalize()),
             'value': s.description or ''}
            for s in product.productSpecifications.all()
            if (s.description or '').strip()
        ]

        data = {
            'id': product.id,
            'slug': product.slug,
            'title': product.title,
            'description': product.description or '',
            'originalPrice': product.orignalPrice,
            'displayPrice': product.displayPrice,
            'discountType': product.discountType,
            'discountBy': product.discountBy,
            'productTags': cls._tags(product),
            'images': cls._images(product),
            'categories': [{'id': c.id, 'label': c.lable, 'value': c.value} for c in product.category.all()],
            'subCategories': [{'id': c.id, 'label': c.lable, 'value': c.value} for c in product.subCategory.all()],
            'specifications': specifications,
            # null stockQuantity = stock not tracked → sellable ("in stock")
            'stock': {
                'inStock': product.stockQuantity is None or product.stockQuantity > 0,
                'stockQuantity': product.stockQuantity,
            },
            'ratingValue': product.ratingValue,
            'totalReviews': product.totalReviews,
            'ratingBreakdown': product.ratingBreakdown or {},
            'viewCount': product.viewCount,
            'label': product.label or '',
            'isActive': product.isActive,
            'business': {
                'id': business.id if business else None,
                'name': business.businessName if business else '',
                'slug': business.slug if business else '',
                'businessType': business.businessType.lable if business and business.businessType else '',
                'city': location.city if location else '',
                'state': location.locationState.name if location and location.locationState else '',
                'pinCode': location.pinCode if location else '',
                'isVerified': bool(business.isVerified) if business else False,
                'ratingValue': business.ratingValue if business else 0.0,
                'totalReviews': business.totalReviews if business else 0,
                'coverImageUrl': (business.coverImageUrl or '') if business else '',
                'since': (business.since or '') if business else '',
                'gst': (business.gst or '') if business else '',
                'whatsapp': (business.whatsapp or '') if business else '',
                'phone': (user_profile.phone or '') if user_profile else '',
                'countryCode': (user_profile.countryCode or '') if user_profile else '',
                'about': ((profile.about if profile and profile.about else None)
                          or (business.bio if business else None) or ''),
                'productCount': business.products.filter(isActive=True).count() if business else 0,
                'avgResponseSeconds': business.avgResponseSeconds if business else None,
            },
        }
        return _ok(data)

    @classmethod
    def getRelatedProductsV3(cls, productId: int, limit: int = _DEFAULT_LIMIT) -> LocalResponse:
        """Products sharing a category/sub-category — plain ORM, no cache."""
        limit = max(1, min(int(limit or _DEFAULT_LIMIT), _MAX_LIMIT))
        product = Product.objects.prefetch_related('category', 'subCategory').filter(id=productId).first()
        if not product:
            return _not_found()

        cat_ids = list(product.category.values_list('id', flat=True))
        sub_ids = list(product.subCategory.values_list('id', flat=True))
        match = Q()
        if cat_ids:
            match |= Q(category__id__in=cat_ids)
        if sub_ids:
            match |= Q(subCategory__id__in=sub_ids)

        base = Product.objects.filter(isActive=True).exclude(id=product.id)
        rows = list(cls._rail_queryset(base.filter(match).distinct())[:limit]) if (cat_ids or sub_ids) else []
        if not rows:
            # nothing shares a category — top trending products as the floor
            rows = list(cls._rail_queryset(base)[:limit])

        items = [cls._card(p) for p in rows]
        return _ok({'items': items, 'total': len(items)})

    @classmethod
    def getBusinessProductsV3(cls, productId: int, limit: int = _DEFAULT_LIMIT) -> LocalResponse:
        """Other products from the same business (rail under the detail page)."""
        limit = max(1, min(int(limit or _DEFAULT_LIMIT), _MAX_LIMIT))
        product = Product.objects.select_related('business').filter(id=productId).first()
        if not product or not product.business:
            return _not_found()

        business = product.business
        rows = list(cls._rail_queryset(
            business.products.filter(isActive=True).exclude(id=product.id)
        )[:limit])

        return _ok({
            'business': {
                'id': business.id,
                'name': business.businessName,
                'slug': business.slug,
                'isVerified': bool(business.isVerified),
            },
            'items': [cls._card(p) for p in rows],
            'total': len(rows),
        })
