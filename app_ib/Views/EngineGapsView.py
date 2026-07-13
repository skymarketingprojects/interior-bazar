"""
EngineGapsView — HTTP layer for the v2.1.1 gap endpoints.

Canonical responder stack (task 19):
- Sync DRF @api_view functions
- @exceptionHandler(responseFunc=ServerResponse, errorMessage=...) wraps each view;
  the decorator maps engine NotFound_/PermissionError_/Conflict_ to 410/403/409 and any
  other exception to a clean envelope. Views return ServerResponse(...) directly.
- ServerResponse + RESPONSE_CODES/RESPONSE_MESSAGES/NAMES constants (no local wrappers).
- AllowAny vs IsAuthenticated permissions; camelCase JSON keys, no serializers.
"""
from datetime import timedelta, date

from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from app_ib.Utils.sse_streamer import EventStreamRenderer

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.Names import NAMES
from app_ib.Utils.EngineConfig import ENTITY_TYPE, TRENDING_PERIOD
from app_ib.decorators.ViewDecorator import exceptionHandler
import app_ib.Controllers.Engine.GapsController as GC


# ==========================================================================
# 1. Trending services
# ==========================================================================
@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def TrendingServicesView(request):
    period = request.GET.get("period", TRENDING_PERIOD.WEEKLY)
    if period not in TRENDING_PERIOD.ALL:
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request, message=RESPONSE_MESSAGES.invalid_period, data={})
    city = request.GET.get("city", "")
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.trending_services(period, city))


# ==========================================================================
# 2. Trending categories
# ==========================================================================
@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def TrendingCategoriesView(request):
    cat_type = request.GET.get("type", "business")
    period = request.GET.get("period", TRENDING_PERIOD.WEEKLY)
    if period not in TRENDING_PERIOD.ALL:
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request, message=RESPONSE_MESSAGES.invalid_period, data={})
    try:
        limit = int(request.GET.get("limit", 12))
    except (ValueError, TypeError):
        limit = 12
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.trending_categories(cat_type, period, limit))


# ==========================================================================
# 3. Trending KPI (platform stats strip)
# ==========================================================================
@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def TrendingKpiView(request):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.trending_kpi())


# ==========================================================================
# 4. Saved check
# ==========================================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def SavedCheckView(request):
    entity_type = request.GET.get("entityType", "")
    object_id = request.GET.get("objectId", "")
    if entity_type not in ENTITY_TYPE.ALL or not object_id:
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request, message=RESPONSE_MESSAGES.entity_object_required, data={})
    try:
        oid = int(object_id)
    except (ValueError, TypeError):
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request, message=RESPONSE_MESSAGES.object_id_must_be_integer, data={})
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.saved_check(request.user, entity_type, oid))


# ==========================================================================
# 5. Recently-viewed clear
# ==========================================================================
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def RecentlyViewedClearView(request):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.recently_viewed_clear(request.user))


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def RecentlyViewedRemoveView(request, row_id):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.recently_viewed_remove(request.user, row_id))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def MyFeedbackListView(request):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.list_my_feedback(request.user))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def NotificationsMarkAllReadView(request):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.notifications_marked_read, data=GC.mark_all_notifications_read(request.user))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ChangePlanView(request):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.plan_change_processed, data=GC.change_plan(request.user, request.data.get("entityType", "business"),
                                   request.data.get("targetPlanId"),
                                   request.data.get("cycleId")))


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def AutogrowthView(request):
    if request.method == "POST":
        return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.keyword_added, data=GC.autogrowth_add(request.user, request.data.get("term", "")))
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.autogrowth_list(request.user))


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def AutogrowthRemoveView(request, keywordId):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.keyword_removed, data=GC.autogrowth_remove(request.user, keywordId))


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def UserSettingsView(request):
    if request.method == "PATCH":
        return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.settings_updated, data=GC.update_user_settings(request.user, request.data))
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.get_user_settings(request.user))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def DeactivateAccountView(request):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.account_deactivated, data=GC.deactivate_account(request.user))


# ==========================================================================
# 6. Dashboard KPIs
# ==========================================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def DashboardKpisView(request):
    try:
        window_days = int(request.GET.get("windowDays", 7))
    except (ValueError, TypeError):
        window_days = 7
    window_days = max(1, min(window_days, 90))
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.dashboard_kpis(request.user, window_days))


# ==========================================================================
# 7. Analytics chart
# ==========================================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def AnalyticsChartView(request):
    from django.utils import timezone
    today = timezone.now().date()
    default_from = today - timedelta(days=29)

    from_str = request.GET.get("from", "")
    to_str = request.GET.get("to", "")
    try:
        from_date = date.fromisoformat(from_str) if from_str else default_from
        to_date = date.fromisoformat(to_str) if to_str else today
    except ValueError:
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request, message=RESPONSE_MESSAGES.date_range_format_error, data={})

    entity_type = request.GET.get("entityType", "") or None
    object_id_str = request.GET.get("objectId", "") or None
    object_id = None
    if object_id_str:
        try:
            object_id = int(object_id_str)
        except (ValueError, TypeError):
            return ServerResponse(response=False, code=RESPONSE_CODES.bad_request, message=RESPONSE_MESSAGES.object_id_must_be_integer, data={})

    if entity_type and entity_type not in ENTITY_TYPE.ALL:
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request, message=RESPONSE_MESSAGES.invalid_entity_type, data={})

    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.analytics_chart(request.user, from_date, to_date, entity_type, object_id))


# ==========================================================================
# 8. Shop + Architect public detail + list views
# ==========================================================================
@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ShopDetailView(request, shopId):
    """GET is public (with isActive filter for non-owners).
    PUT/PATCH/DELETE require auth and delegate to CrudController."""
    if request.method == "GET":
        return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.get_shop(shopId, user=request.user))
    # write methods — require auth
    if not request.user or not request.user.is_authenticated:
        return ServerResponse(response=False, code=RESPONSE_CODES.auth_error, message=RESPONSE_MESSAGES.authentication_required, data={})
    from app_ib.Controllers.Engine.CrudController import CRUD_CONTROLLER
    if request.method == "DELETE":
        CRUD_CONTROLLER.delete_shop(request.user, shopId)
        return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.shop_deleted, data={})
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.shop_updated, data=CRUD_CONTROLLER.update_shop(request.user, shopId, request.data))


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ShopBySlugView(request, slug):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.get_shop_by_slug(slug, user=request.user))


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ShopsListView(request):
    city = request.GET.get("city", "")
    shop_type = request.GET.get("shopType", "")
    category = request.GET.get("category", "")
    search = request.GET.get("search", "")
    sort = request.GET.get("sort", "trending")
    try:
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("pageSize", 20))
    except (ValueError, TypeError):
        page, page_size = 1, 20
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.list_shops(city, shop_type, search, sort, page, page_size, category=category))


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ArchitectDetailView(request, architectId):
    if request.method == "GET":
        return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.get_architect(architectId, user=request.user))
    if not request.user or not request.user.is_authenticated:
        return ServerResponse(response=False, code=RESPONSE_CODES.auth_error, message=RESPONSE_MESSAGES.authentication_required, data={})
    from app_ib.Controllers.Engine.CrudController import CRUD_CONTROLLER
    if request.method == "DELETE":
        CRUD_CONTROLLER.delete_architect(request.user, architectId)
        return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.architect_deleted, data={})
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.architect_updated, data=CRUD_CONTROLLER.update_architect(request.user, architectId, request.data))


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ArchitectBySlugView(request, slug):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.get_architect_by_slug(slug, user=request.user))


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ArchitectsListView(request):
    city = request.GET.get("city", "")
    category = request.GET.get("category", "")
    search = request.GET.get("search", "")
    sort = request.GET.get("sort", "trending")
    try:
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("pageSize", 20))
    except (ValueError, TypeError):
        page, page_size = 1, 20
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.list_architects(city, search, sort, page, page_size, category=category))


# ==========================================================================
# 8e. Business public detail (core + related offerings + review summary)
# ==========================================================================
@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def BusinessDetailView(request, businessId):
    """GET is public; PUT/PATCH/DELETE require auth and delegate to CrudController
    (ownership-gated). DELETE is a soft delete (isActive=False)."""
    if request.method == "GET":
        return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.get_business(businessId, user=request.user))
    if not request.user or not request.user.is_authenticated:
        return ServerResponse(response=False, code=RESPONSE_CODES.auth_error, message=RESPONSE_MESSAGES.authentication_required, data={})
    from app_ib.Controllers.Engine.CrudController import CRUD_CONTROLLER
    if request.method == "DELETE":
        CRUD_CONTROLLER.delete_business(request.user, businessId)
        return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.engine_business_deleted, data={})
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.engine_business_updated, data=CRUD_CONTROLLER.update_business(request.user, businessId, request.data))


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def BusinessBySlugView(request, slug):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.get_business_by_slug(slug, user=request.user))


# --- Per-business offering lists (paginated) — lazy-loaded by the v3 detail tabs ---
@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def BusinessProductsView(request, businessId):
    page, page_size = _list_paging(request)
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.get_business_products(businessId, page, page_size))


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def BusinessServicesView(request, businessId):
    page, page_size = _list_paging(request)
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.get_business_services(businessId, page, page_size))


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def BusinessCataloguesView(request, businessId):
    page, page_size = _list_paging(request)
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.get_business_catalogues(businessId, page, page_size))


# ==========================================================================
# 8a-bis. Public lists: businesses / products / services / catalogues
#         Same envelope/params as shops/ & architects/ (item 8).
# ==========================================================================
def _list_paging(request):
    try:
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("pageSize", 20))
    except (ValueError, TypeError):
        page, page_size = 1, 20
    return page, page_size


def _float_param(request, key):
    raw = request.GET.get(key, "")
    try:
        return float(raw) if raw != "" else None
    except (ValueError, TypeError):
        return None


def _flag_param(request, key):
    return request.GET.get(key, "").lower() in ("1", "true")


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def BusinessesListView(request):
    city = request.GET.get("city", "")
    business_type = request.GET.get("type", "")
    category = request.GET.get("category", "")
    verified = _flag_param(request, "verified")
    search = request.GET.get("search", "")
    sort = request.GET.get("sort", "trending")
    page, page_size = _list_paging(request)
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.list_businesses(city, business_type, search, sort, page, page_size,
                                       category=category, verified=verified))


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ProductsListView(request):
    city = request.GET.get("city", "")
    category = request.GET.get("category", "")
    search = request.GET.get("search", "")
    sort = request.GET.get("sort", "trending")
    page, page_size = _list_paging(request)
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.list_products(city, category, search, sort, page, page_size,
                                     min_price=_float_param(request, "minPrice"),
                                     max_price=_float_param(request, "maxPrice"),
                                     verified=_flag_param(request, "verified"),
                                     in_stock=_flag_param(request, "inStock"),
                                     rating_min=_float_param(request, "ratingMin")))


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ProductCategoriesView(request):
    # Product category taxonomy (value/label/count) for the products filter sidebar.
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.list_product_categories())


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ServiceCategoriesView(request):
    # Service category taxonomy (value/label/count) for the services filter bar.
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.list_service_categories())


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def BusinessCategoriesView(request):
    # Business category taxonomy (value/label/count) for the businesses filter bar.
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.list_business_categories())


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ShopCategoriesView(request):
    # Shop category taxonomy (value=tag slug/label/count) for the shops filter bar.
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.list_shop_categories())


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ArchitectCategoriesView(request):
    # Architect specialization taxonomy (value=tag slug/label/count) for the architects filter bar.
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.list_architect_categories())


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ServicesListView(request):
    city = request.GET.get("city", "")
    category = request.GET.get("category", "")
    search = request.GET.get("search", "")
    sort = request.GET.get("sort", "trending")
    page, page_size = _list_paging(request)
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.list_services(city, category, search, sort, page, page_size,
                                     min_price=_float_param(request, "minPrice"),
                                     max_price=_float_param(request, "maxPrice"),
                                     verified=_flag_param(request, "verified"),
                                     rating_min=_float_param(request, "ratingMin")))


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def CataloguesListView(request):
    city = request.GET.get("city", "")
    category = request.GET.get("category", "")
    search = request.GET.get("search", "")
    sort = request.GET.get("sort", "trending")
    page, page_size = _list_paging(request)
    year_raw = request.GET.get("year", "")
    year = int(year_raw) if year_raw.isdigit() else None
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.list_catalogues(city, category, search, sort, page, page_size,
                                       verified=_flag_param(request, "verified"),
                                       year=year, free=_flag_param(request, "free")))


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def CatalogueDetailView(request, slugOrId):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.catalogue_detail(slugOrId))


# ==========================================================================
# 8b. Authenticated owner lists (shops/mine/, architects/mine/)
# ==========================================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def MyShopsView(request):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.my_shops(request.user))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def MyArchitectsView(request):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.my_architects(request.user))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def MyPlansView(request):
    # Buying history: union of the user's business/shop/architect plans (Prompt 6).
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.my_plans(request.user))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def MyInvoicesView(request):
    # Billing / invoice history: TransectionData rows matched to the user's plans.
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.my_invoices(request.user))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def MyActivityView(request):
    # Recent view + click event feed for the logged-in user.
    try:
        limit = int(request.GET.get("limit", 30))
    except (ValueError, TypeError):
        limit = 30
    limit = max(1, min(limit, 100))
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.my_activity(request.user, limit=limit))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def MyEngagementView(request):
    # Inbound recent-activity feed: actions OTHER users took on the logged-in
    # seller's own entities (viewed/saved/enquired about your product/shop/etc.).
    try:
        limit = int(request.GET.get("limit", 30))
    except (ValueError, TypeError):
        limit = 30
    limit = max(1, min(limit, 100))
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.engagement_feed(request.user, limit=limit))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def MyEngagementReadView(request):
    # Mark all of the seller's inbound-engagement rows as read.
    updated = GC.engagement_mark_read(request.user)
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data={NAMES.UPDATED: updated})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def MyQuotationsView(request):
    # Leads received by the logged-in seller's business.
    try:
        limit = int(request.GET.get("limit", 50))
    except (ValueError, TypeError):
        limit = 50
    limit = max(1, min(limit, 200))
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.my_quotations(request.user, limit=limit))


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def SupportConfigView(request):
    # Public support/contact channels (single source of truth — task 75).
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.support_config())


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def BrandLogoPublicView(request):
    # Public: today's active brand logo + tagline (task 27).
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.brand_logo())


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def TeamMembersView(request):
    # Public About-page team grid (task 77).
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.team_members())


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def HelpContentView(request):
    # Public help-centre content: FAQs, topics, tutorials (task 76).
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.help_content())


@api_view(["GET", "POST"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def SupportTicketsView(request):
    # POST raise a ticket (auth optional; anon needs an email); GET the user's tickets.
    if request.method == "POST":
        return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ticket_raised, data=GC.create_ticket(request.user, request.data))
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.my_tickets(request.user))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def QuotationCreateView(request):
    # Create a seller-built quotation document (task 63).
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.quotation_saved, data=GC.create_quotation(request.user, request.data))


@api_view(["PATCH", "PUT"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def QuotationUpdateView(request, quotationId):
    # Update an owned quotation (owner-gated; totals recomputed server-side).
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.quotation_updated, data=GC.update_quotation(request.user, quotationId, request.data))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def QuotationStatusView(request, quotationId):
    # Transition an owned quotation's status (sent/viewed/accepted/declined).
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.quotation_status_updated, data=GC.set_quotation_status(request.user, quotationId, request.data.get("status", "")))


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def PlanTemplatesView(request):
    # Public Subscription catalogue (optionally ?entityType=) — each row carries
    # `key` (=Subscription.tag) so the v3 checkout resolves a card to a real plan id.
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.plan_templates(request.GET.get("entityType", "")))


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ServerTimeView(request):
    # Backend-authoritative clock (Prompt 12): server now + login-time anchor.
    user = request.user if getattr(request.user, "is_authenticated", False) else None
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.server_time(user))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def PaymentRecheckView(request):
    # Manual single-transaction re-verify (Prompt 10): re-runs CheckPaymentStatus for
    # ONE transaction and returns just that payment's card so a single card refreshes.
    from asgiref.sync import async_to_sync
    from app_ib.Controllers.PaymentGateway.PaymentGatewayController import PaymentGatewayController
    txn = request.data.get("transactionId")
    if not txn:
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request, message=RESPONSE_MESSAGES.transaction_id_required, data={})
    async_to_sync(PaymentGatewayController.CheckPaymentStatus)(txn, {})
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.payment_card(request.user, txn))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ManualPlanView(request):
    # Manual (offline) plan purchase: the buyer pays by bank/UPI transfer and submits
    # their transaction id. Creates the chosen entity plan INACTIVE (pending backend
    # verification) and flips the buyer to a seller immediately so they can open the
    # seller dashboard. Returns the freshly-created (pending) plan card.
    plan_id = request.data.get("planId")
    cycle_id = request.data.get("cycleId")
    txn = request.data.get("transactionId")
    proof_url = request.data.get("proofUrl", "")
    if not plan_id:
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request, message=RESPONSE_MESSAGES.plan_id_required, data={})
    if not txn:
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request, message=RESPONSE_MESSAGES.transaction_id_required, data={})
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.create_manual_plan(request.user, plan_id, txn, proof_url, cycle_id))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def UpgradePreviewView(request):
    # Validate an upgrade + return the prorated settlement (Prompt 9). Always 200;
    # read data.allowed / data.settleAmount / data.reason on the client.
    from asgiref.sync import async_to_sync
    from app_ib.Controllers.Plans.PlanController import PLAN_CONTROLLER
    resp = async_to_sync(PLAN_CONTROLLER.PreviewUpgrade)(
        request.user, request.data.get("entityType"), request.data.get("targetPlanId"))
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=resp.message, data=resp.data)


# ==========================================================================
# 8c. Entity resolve (public, AllowAny)
# ==========================================================================
@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ResolveEntityView(request, entityType, slug):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.resolve_entity(entityType, slug))


# ==========================================================================
# 9. Video CRUD
# ==========================================================================
@api_view(["GET", "POST"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def VideoListCreateView(request, entityType, objectId):
    if entityType not in ENTITY_TYPE.ALL:
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request, message=RESPONSE_MESSAGES.unsupported_entity_type, data={})
    if request.method == "POST":
        if not request.user or not request.user.is_authenticated:
            return ServerResponse(response=False, code=RESPONSE_CODES.auth_error, message=RESPONSE_MESSAGES.authentication_required, data={})
        return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.video_created, data=GC.create_video(request.user, entityType, objectId, request.data))
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.list_videos(entityType, objectId))


@api_view(["PUT", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def VideoUpdateDeleteView(request, videoId):
    if request.method == "DELETE":
        GC.delete_video(request.user, videoId)
        return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.video_deleted, data={})
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.video_updated, data=GC.update_video(request.user, videoId, request.data))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def VideoSetPrimaryView(request, videoId):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.video_set_primary, data=GC.set_primary_video(request.user, videoId))


# ==========================================================================
# 10. Leads
# ==========================================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def LeadsPrioritizedView(request):
    business_id = request.GET.get("businessId")
    if business_id:
        try:
            business_id = int(business_id)
        except (ValueError, TypeError):
            return ServerResponse(response=False, code=RESPONSE_CODES.bad_request, message=RESPONSE_MESSAGES.business_id_must_be_integer, data={})
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.prioritized_leads(request.user, business_id))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def LeadAcceptView(request, leadId):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.accept_lead(request.user, leadId))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def LeadStageView(request, leadId):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.lead_stage_updated, data=GC.set_lead_stage(request.user, leadId, request.data.get("stage", "")))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def LeadDeclineView(request, leadId):
    reason = (request.data or {}).get("reason", "")
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.decline_lead(request.user, leadId, reason))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def LeadManualCreateView(request):
    """Seller-logged off-platform enquiry (dashboard '+ Enquiry' panel)."""
    d = request.data or {}
    if not (d.get("buyerName") or "").strip() or not (d.get("lookingFor") or "").strip():
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request, message=RESPONSE_MESSAGES.buyer_name_looking_for_required, data={})
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.lead_created, data=GC.create_manual_lead(request.user, d))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def LeadCreateView(request):
    """Buyer-facing enquiry/lead create — universal connect wizard."""
    if not request.data.get("intent"):
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request, message=RESPONSE_MESSAGES.intent_required, data={})
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.lead_created, data=GC.create_lead(request.user, request.data))


# ==========================================================================
# 11. Platform ads
# ==========================================================================
@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def AdsListView(request):
    page_slug = request.GET.get("page", "")
    placement = request.GET.get("placement", "")
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.get_ads(page_slug, placement))


@api_view(["POST"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def AdClickView(request, adId):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.click_ad(adId))


# ==========================================================================
# 16. Credential CRUD — Award + ProcessStep + Expertise (Phase 1)
# ==========================================================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def AwardCreateView(request):
    """POST /engine/credentials/award/ — create an Award row for an owned entity."""
    # ValueError carries a specific validation message (400); NotFound_/PermissionError_
    # bubble to the decorator (410/403).
    try:
        data = GC.create_award(request.user, request.data)
    except ValueError as e:
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request, message=str(e), data={})
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.award_created, data=data)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def AwardUpdateDeleteView(request, awardId):
    """PATCH /engine/credentials/award/<awardId>/ — partial update.
    DELETE /engine/credentials/award/<awardId>/ — soft delete (isActive=False)."""
    if request.method == "DELETE":
        GC.delete_award(request.user, awardId)
        return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.award_deleted, data={})
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.award_updated, data=GC.update_award(request.user, awardId, request.data))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ProcessStepCreateView(request):
    """POST /engine/credentials/process-step/ — create a ProcessStep for an owned entity."""
    try:
        data = GC.create_process_step(request.user, request.data)
    except ValueError as e:
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request, message=str(e), data={})
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.process_step_created, data=data)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ProcessStepUpdateDeleteView(request, stepId):
    """PATCH /engine/credentials/process-step/<stepId>/ — partial update.
    DELETE /engine/credentials/process-step/<stepId>/ — soft delete."""
    if request.method == "DELETE":
        GC.delete_process_step(request.user, stepId)
        return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.process_step_deleted, data={})
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.process_step_updated, data=GC.update_process_step(request.user, stepId, request.data))


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ExpertiseSetView(request):
    """PUT /engine/credentials/expertise/ — set the entity's expertiseTags.
    Body: {entityType, entityId, tags: [string, ...]}."""
    try:
        data = GC.set_expertise(request.user, request.data)
    except ValueError as e:
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request, message=str(e), data={})
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.expertise_updated, data=data)


# ==========================================================================
# 17. Recently-viewed summary
# ==========================================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def RecentlyViewedSummaryView(request):
    """GET /engine/recently-viewed/summary/ — facets, KPIs, continue banner."""
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.recently_viewed_summary(request.user))


# ==========================================================================
# 12. SSE ?token= auth — patched UserStreamView
# ==========================================================================
def _resolve_token_user(token_str):
    """Validate a JWT access token string and return the user, or None."""
    try:
        from rest_framework_simplejwt.authentication import JWTAuthentication
        jwt_auth = JWTAuthentication()
        validated = jwt_auth.get_validated_token(token_str.encode())
        return jwt_auth.get_user(validated)
    except Exception:
        return None


# ==========================================================================
# Phase 2 — Session management (my/sessions/ + my/sessions/<id>/revoke/)
# ==========================================================================

def _get_sjti_from_token(request) -> str:
    """Extract the 'sjti' claim from the validated access token payload.

    DRF SimpleJWT stores the decoded token payload on request.auth (a
    rest_framework_simplejwt.tokens.AccessToken instance when JWTAuthentication
    is used). We read .payload; fallback: decode manually.
    """
    try:
        auth = getattr(request, "auth", None)
        if auth is not None and hasattr(auth, "payload"):
            return str(auth.payload.get("sjti", "") or "")
        # Fallback: try reading from token payload directly
        if auth is not None and hasattr(auth, "get"):
            return str(auth.get("sjti", "") or "")
    except Exception:
        pass
    return ""


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def MySessionsView(request):
    """GET /engine/my/sessions/
    Returns active sessions for the authenticated user.
    Marks the session matching the caller's access token as isCurrent.
    """
    current_jti = _get_sjti_from_token(request)
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.my_sessions(request.user, current_jti=current_jti or None))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def RevokeSessionView(request, sessionId):
    """POST /engine/my/sessions/<sessionId>/revoke/
    Revoke a single active session owned by the authenticated user.
    Also blacklists the associated refresh token (best-effort).
    """
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.revoke_session(request.user, sessionId))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def RevokeAllSessionsView(request):
    """POST /engine/my/sessions/revoke-all/ — revoke every session except the
    caller's current one ("Sign out everywhere", task 81)."""
    current_jti = _get_sjti_from_token(request)
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.sessions_signed_out, data=GC.revoke_all_other_sessions(request.user, current_jti or None))


# ==========================================================================
# 12. SSE ?token= auth — patched UserStreamView
# Raw StreamingHttpResponse — intentionally NOT wrapped by @exceptionHandler
# (server-sent events must stream, not return a JSON envelope).
# ==========================================================================

@api_view(["GET"])
@permission_classes([AllowAny])
@renderer_classes([EventStreamRenderer])
def UserStreamTokenView(request):
    """Unified SSE stream — accepts Bearer header OR ?token= query param.
    This view replaces UserStreamView in engine_urls.py for the auth-aware SSE.
    """
    from django.http import StreamingHttpResponse
    from app_ib.models import Notification, FeedEvent, Message, Conversation
    from app_ib.Utils.sse_streamer import sse_multiplex, user_channels
    from django.db.models import Q

    # resolve user: header (already done by DRF) or ?token=
    user = request.user if (request.user and request.user.is_authenticated) else None
    if user is None:
        token_str = request.GET.get("token", "")
        if token_str:
            user = _resolve_token_user(token_str)

    if user is None or not user.is_authenticated:
        from app_ib.Utils.ServerResponse import ServerResponse
        return ServerResponse(response=False, code=RESPONSE_CODES.auth_error,
                              message="authentication required", data={})

    once = request.GET.get("once") in ("1", "true")
    uid = user.id

    snapshot = []
    for n in Notification.objects.filter(user=user).order_by("-timestamp")[:50]:
        snapshot.append(("notification", {
            "id": n.id, "type": n.type, "title": n.title, "body": n.body,
            "groupCount": n.groupCount, "timestamp": n.timestamp.isoformat()}))

    conv_ids = list(Conversation.objects.filter(Q(clientUser=user) | Q(businessUser=user))
                    .values_list("id", flat=True))
    from app_ib.Controllers.Engine.ChatController import CHAT_CONTROLLER
    for m in (Message.objects.filter(conversation_id__in=conv_ids, isRead=False)
              .exclude(sender_id=uid).select_related("sender", "sender__user_profile")
              .order_by("-id")[:30]):
        snapshot.append(("chat", {"conversationId": m.conversation_id, "messageId": m.id,
                                  "senderId": m.sender_id, "body": m.body,
                                  "createdAt": m.createdAt.isoformat(),
                                  "senderName": CHAT_CONTROLLER._display_name(m.sender)}))

    for e in reversed(list(FeedEvent.objects.order_by("-timestamp")[:6])):
        snapshot.append(("feed", {"id": e.id, "eventType": e.eventType, "template": e.template,
                                  "city": e.city, "timestamp": e.timestamp.isoformat()}))

    resp = StreamingHttpResponse(
        sse_multiplex(snapshot, user_channels(uid), once=once),
        content_type="text/event-stream")
    resp["Cache-Control"] = "no-cache"
    resp["X-Accel-Buffering"] = "no"
    return resp


# ==========================================================================
# Phase 3 — 1. Related items
# ==========================================================================
@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def RelatedItemsView(request, entityType, objectId):
    try:
        limit = int(request.GET.get("limit", 12))
    except (ValueError, TypeError):
        limit = 12
    limit = max(1, min(limit, 50))
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.related_items(entityType, objectId, limit))


# ==========================================================================
# Phase 3 — 2. Newsletter subscribe
# ==========================================================================
@api_view(["POST"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def NewsletterSubscribeView(request):
    email = (request.data.get("email") or "").strip()
    if not email:
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request, message=RESPONSE_MESSAGES.email_required, data={})
    source = request.data.get("source", "blog")
    user = request.user if request.user and request.user.is_authenticated else None
    try:
        data = GC.newsletter_subscribe(email, source, user)
    except ValueError as e:
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request, message=str(e), data={})
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=data)


# ==========================================================================
# Phase 3 — 3. Blog featured
# ==========================================================================
@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def FeaturedBlogsView(request):
    try:
        limit = int(request.GET.get("limit", 1))
    except (ValueError, TypeError):
        limit = 1
    limit = max(1, min(limit, 20))
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.featured_blogs(limit))


# ==========================================================================
# Phase 3 — 4. Catalogue trending
# ==========================================================================
@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def TrendingCataloguesView(request):
    period = request.GET.get("period", "")
    city = request.GET.get("city", "")
    try:
        limit = int(request.GET.get("limit", 12))
    except (ValueError, TypeError):
        limit = 12
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.trending_catalogues(period, city, limit))


# ==========================================================================
# Phase 3 — 5. Engine my/profile/
# ==========================================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def MyProfileView(request):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.ok, data=GC.my_profile(request.user))


# ==========================================================================
# my/change-password/ — authenticated password change (v3 dashboard security)
# ==========================================================================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.engine_error)
def ChangePasswordView(request):
    """POST /engine/my/change-password/
    Body: { currentPassword, newPassword, confirmPassword }
    Verifies the current password then updates it. v3-only.
    """
    # ValueError = the specific validation reason (wrong current password / mismatch),
    # surfaced to the user with 400; other failures bubble to the decorator.
    try:
        data = GC.change_password(request.user, request.data)
    except ValueError as e:
        return ServerResponse(response=False, code=RESPONSE_CODES.bad_request, message=str(e), data={})
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=RESPONSE_MESSAGES.password_updated, data=data)
