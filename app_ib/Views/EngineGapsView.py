"""
EngineGapsView — HTTP layer for the v2.1.1 gap endpoints.

Follows the same conventions as EngineView / EngineCrudView:
- Sync DRF @api_view functions
- _ok(data) / _err(e) wrappers
- AllowAny vs IsAuthenticated permissions
- camelCase JSON keys, no serializers
"""
from datetime import timedelta, date

from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from app_ib.Utils.sse_streamer import EventStreamRenderer

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.EngineConfig import ENTITY_TYPE, TRENDING_PERIOD
from app_ib.Controllers.Engine.CrudController import NotFound_, PermissionError_, Conflict_
import app_ib.Controllers.Engine.GapsController as GC


def _ok(data, msg="ok"):
    return ServerResponse(response=True, code=RESPONSE_CODES.success, message=msg, data=data)


def _err(e):
    if isinstance(e, NotFound_):
        return ServerResponse(response=False, code=RESPONSE_CODES.not_exist, message=str(e), data={})
    if isinstance(e, PermissionError_):
        return ServerResponse(response=False, code=RESPONSE_CODES.forbidden, message=str(e), data={})
    if isinstance(e, Conflict_):
        return ServerResponse(response=False, code=RESPONSE_CODES.conflict, message=str(e), data={})
    return ServerResponse(response=False, code=RESPONSE_CODES.error, message=str(e), data={})


def _bad(msg="bad request"):
    return ServerResponse(response=False, code=RESPONSE_CODES.bad_request, message=msg, data={})


# ==========================================================================
# 1. Trending services
# ==========================================================================
@api_view(["GET"])
@permission_classes([AllowAny])
def TrendingServicesView(request):
    period = request.GET.get("period", TRENDING_PERIOD.WEEKLY)
    if period not in TRENDING_PERIOD.ALL:
        return _bad("invalid period")
    city = request.GET.get("city", "")
    return _ok(GC.trending_services(period, city))


# ==========================================================================
# 2. Trending categories
# ==========================================================================
@api_view(["GET"])
@permission_classes([AllowAny])
def TrendingCategoriesView(request):
    cat_type = request.GET.get("type", "business")
    period = request.GET.get("period", TRENDING_PERIOD.WEEKLY)
    if period not in TRENDING_PERIOD.ALL:
        return _bad("invalid period")
    try:
        limit = int(request.GET.get("limit", 12))
    except (ValueError, TypeError):
        limit = 12
    return _ok(GC.trending_categories(cat_type, period, limit))


# ==========================================================================
# 3. Trending KPI (platform stats strip)
# ==========================================================================
@api_view(["GET"])
@permission_classes([AllowAny])
def TrendingKpiView(request):
    return _ok(GC.trending_kpi())


# ==========================================================================
# 4. Saved check
# ==========================================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def SavedCheckView(request):
    entity_type = request.GET.get("entityType", "")
    object_id = request.GET.get("objectId", "")
    if entity_type not in ENTITY_TYPE.ALL or not object_id:
        return _bad("entityType and objectId required")
    try:
        oid = int(object_id)
    except (ValueError, TypeError):
        return _bad("objectId must be an integer")
    return _ok(GC.saved_check(request.user, entity_type, oid))


# ==========================================================================
# 5. Recently-viewed clear
# ==========================================================================
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def RecentlyViewedClearView(request):
    return _ok(GC.recently_viewed_clear(request.user))


# ==========================================================================
# 6. Dashboard KPIs
# ==========================================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def DashboardKpisView(request):
    try:
        window_days = int(request.GET.get("windowDays", 7))
    except (ValueError, TypeError):
        window_days = 7
    window_days = max(1, min(window_days, 90))
    return _ok(GC.dashboard_kpis(request.user, window_days))


# ==========================================================================
# 7. Analytics chart
# ==========================================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
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
        return _bad("from/to must be YYYY-MM-DD")

    entity_type = request.GET.get("entityType", "") or None
    object_id_str = request.GET.get("objectId", "") or None
    object_id = None
    if object_id_str:
        try:
            object_id = int(object_id_str)
        except (ValueError, TypeError):
            return _bad("objectId must be an integer")

    if entity_type and entity_type not in ENTITY_TYPE.ALL:
        return _bad("invalid entityType")

    try:
        return _ok(GC.analytics_chart(request.user, from_date, to_date, entity_type, object_id))
    except Exception as e:
        return _err(e)


# ==========================================================================
# 8. Shop + Architect public detail + list views
# ==========================================================================
@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([AllowAny])
def ShopDetailView(request, shopId):
    """GET is public (with isActive filter for non-owners).
    PUT/PATCH/DELETE require auth and delegate to CrudController."""
    if request.method == "GET":
        try:
            return _ok(GC.get_shop(shopId, user=request.user))
        except Exception as e:
            return _err(e)
    # write methods — require auth
    if not request.user or not request.user.is_authenticated:
        return ServerResponse(response=False, code=RESPONSE_CODES.auth_error,
                              message="authentication required", data={})
    from app_ib.Controllers.Engine.CrudController import CRUD_CONTROLLER
    try:
        if request.method == "DELETE":
            CRUD_CONTROLLER.delete_shop(request.user, shopId)
            return _ok({}, "Shop deleted")
        return _ok(CRUD_CONTROLLER.update_shop(request.user, shopId, request.data), "Shop updated")
    except Exception as e:
        return _err(e)


@api_view(["GET"])
@permission_classes([AllowAny])
def ShopBySlugView(request, slug):
    try:
        return _ok(GC.get_shop_by_slug(slug, user=request.user))
    except Exception as e:
        return _err(e)


@api_view(["GET"])
@permission_classes([AllowAny])
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
    return _ok(GC.list_shops(city, shop_type, search, sort, page, page_size, category=category))


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([AllowAny])
def ArchitectDetailView(request, architectId):
    if request.method == "GET":
        try:
            return _ok(GC.get_architect(architectId, user=request.user))
        except Exception as e:
            return _err(e)
    if not request.user or not request.user.is_authenticated:
        return ServerResponse(response=False, code=RESPONSE_CODES.auth_error,
                              message="authentication required", data={})
    from app_ib.Controllers.Engine.CrudController import CRUD_CONTROLLER
    try:
        if request.method == "DELETE":
            CRUD_CONTROLLER.delete_architect(request.user, architectId)
            return _ok({}, "Architect deleted")
        return _ok(CRUD_CONTROLLER.update_architect(request.user, architectId, request.data),
                   "Architect updated")
    except Exception as e:
        return _err(e)


@api_view(["GET"])
@permission_classes([AllowAny])
def ArchitectBySlugView(request, slug):
    try:
        return _ok(GC.get_architect_by_slug(slug, user=request.user))
    except Exception as e:
        return _err(e)


@api_view(["GET"])
@permission_classes([AllowAny])
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
    return _ok(GC.list_architects(city, search, sort, page, page_size, category=category))


# ==========================================================================
# 8e. Business public detail (core + related offerings + review summary)
# ==========================================================================
@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([AllowAny])
def BusinessDetailView(request, businessId):
    """GET is public; PUT/PATCH/DELETE require auth and delegate to CrudController
    (ownership-gated). DELETE is a soft delete (isActive=False)."""
    if request.method == "GET":
        try:
            return _ok(GC.get_business(businessId, user=request.user))
        except Exception as e:
            return _err(e)
    if not request.user or not request.user.is_authenticated:
        return ServerResponse(response=False, code=RESPONSE_CODES.auth_error,
                              message="authentication required", data={})
    from app_ib.Controllers.Engine.CrudController import CRUD_CONTROLLER
    try:
        if request.method == "DELETE":
            CRUD_CONTROLLER.delete_business(request.user, businessId)
            return _ok({}, "Business deleted")
        return _ok(CRUD_CONTROLLER.update_business(request.user, businessId, request.data),
                   "Business updated")
    except Exception as e:
        return _err(e)


@api_view(["GET"])
@permission_classes([AllowAny])
def BusinessBySlugView(request, slug):
    try:
        return _ok(GC.get_business_by_slug(slug, user=request.user))
    except Exception as e:
        return _err(e)


# --- Per-business offering lists (paginated) — lazy-loaded by the v3 detail tabs ---
@api_view(["GET"])
@permission_classes([AllowAny])
def BusinessProductsView(request, businessId):
    page, page_size = _list_paging(request)
    try:
        return _ok(GC.get_business_products(businessId, page, page_size))
    except Exception as e:
        return _err(e)


@api_view(["GET"])
@permission_classes([AllowAny])
def BusinessServicesView(request, businessId):
    page, page_size = _list_paging(request)
    try:
        return _ok(GC.get_business_services(businessId, page, page_size))
    except Exception as e:
        return _err(e)


@api_view(["GET"])
@permission_classes([AllowAny])
def BusinessCataloguesView(request, businessId):
    page, page_size = _list_paging(request)
    try:
        return _ok(GC.get_business_catalogues(businessId, page, page_size))
    except Exception as e:
        return _err(e)


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
def BusinessesListView(request):
    city = request.GET.get("city", "")
    business_type = request.GET.get("type", "")
    category = request.GET.get("category", "")
    verified = _flag_param(request, "verified")
    search = request.GET.get("search", "")
    sort = request.GET.get("sort", "trending")
    page, page_size = _list_paging(request)
    return _ok(GC.list_businesses(city, business_type, search, sort, page, page_size,
                                  category=category, verified=verified))


@api_view(["GET"])
@permission_classes([AllowAny])
def ProductsListView(request):
    city = request.GET.get("city", "")
    category = request.GET.get("category", "")
    search = request.GET.get("search", "")
    sort = request.GET.get("sort", "trending")
    page, page_size = _list_paging(request)
    return _ok(GC.list_products(city, category, search, sort, page, page_size,
                                min_price=_float_param(request, "minPrice"),
                                max_price=_float_param(request, "maxPrice"),
                                verified=_flag_param(request, "verified"),
                                in_stock=_flag_param(request, "inStock"),
                                rating_min=_float_param(request, "ratingMin")))


@api_view(["GET"])
@permission_classes([AllowAny])
def ProductCategoriesView(request):
    # Product category taxonomy (value/label/count) for the products filter sidebar.
    return _ok(GC.list_product_categories())


@api_view(["GET"])
@permission_classes([AllowAny])
def ServiceCategoriesView(request):
    # Service category taxonomy (value/label/count) for the services filter bar.
    return _ok(GC.list_service_categories())


@api_view(["GET"])
@permission_classes([AllowAny])
def BusinessCategoriesView(request):
    # Business category taxonomy (value/label/count) for the businesses filter bar.
    return _ok(GC.list_business_categories())


@api_view(["GET"])
@permission_classes([AllowAny])
def ShopCategoriesView(request):
    # Shop category taxonomy (value=tag slug/label/count) for the shops filter bar.
    return _ok(GC.list_shop_categories())


@api_view(["GET"])
@permission_classes([AllowAny])
def ArchitectCategoriesView(request):
    # Architect specialization taxonomy (value=tag slug/label/count) for the architects filter bar.
    return _ok(GC.list_architect_categories())


@api_view(["GET"])
@permission_classes([AllowAny])
def ServicesListView(request):
    city = request.GET.get("city", "")
    category = request.GET.get("category", "")
    search = request.GET.get("search", "")
    sort = request.GET.get("sort", "trending")
    page, page_size = _list_paging(request)
    return _ok(GC.list_services(city, category, search, sort, page, page_size,
                                min_price=_float_param(request, "minPrice"),
                                max_price=_float_param(request, "maxPrice"),
                                verified=_flag_param(request, "verified"),
                                rating_min=_float_param(request, "ratingMin")))


@api_view(["GET"])
@permission_classes([AllowAny])
def CataloguesListView(request):
    city = request.GET.get("city", "")
    category = request.GET.get("category", "")
    search = request.GET.get("search", "")
    sort = request.GET.get("sort", "trending")
    page, page_size = _list_paging(request)
    return _ok(GC.list_catalogues(city, category, search, sort, page, page_size,
                                  verified=_flag_param(request, "verified")))


@api_view(["GET"])
@permission_classes([AllowAny])
def CatalogueDetailView(request, slugOrId):
    try:
        return _ok(GC.catalogue_detail(slugOrId))
    except Exception as e:
        return _err(e)


# ==========================================================================
# 8b. Authenticated owner lists (shops/mine/, architects/mine/)
# ==========================================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def MyShopsView(request):
    try:
        return _ok(GC.my_shops(request.user))
    except Exception as e:
        return _err(e)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def MyArchitectsView(request):
    try:
        return _ok(GC.my_architects(request.user))
    except Exception as e:
        return _err(e)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def MyPlansView(request):
    # Buying history: union of the user's business/shop/architect plans (Prompt 6).
    try:
        return _ok(GC.my_plans(request.user))
    except Exception as e:
        return _err(e)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def MyInvoicesView(request):
    # Billing / invoice history: TransectionData rows matched to the user's plans.
    try:
        return _ok(GC.my_invoices(request.user))
    except Exception as e:
        return _err(e)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def MyActivityView(request):
    # Recent view + click event feed for the logged-in user.
    try:
        try:
            limit = int(request.GET.get("limit", 30))
        except (ValueError, TypeError):
            limit = 30
        limit = max(1, min(limit, 100))
        return _ok(GC.my_activity(request.user, limit=limit))
    except Exception as e:
        return _err(e)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def MyEngagementView(request):
    # Inbound recent-activity feed: actions OTHER users took on the logged-in
    # seller's own entities (viewed/saved/enquired about your product/shop/etc.).
    try:
        try:
            limit = int(request.GET.get("limit", 30))
        except (ValueError, TypeError):
            limit = 30
        limit = max(1, min(limit, 100))
        return _ok(GC.engagement_feed(request.user, limit=limit))
    except Exception as e:
        return _err(e)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def MyEngagementReadView(request):
    # Mark all of the seller's inbound-engagement rows as read.
    try:
        updated = GC.engagement_mark_read(request.user)
        return _ok({"updated": updated})
    except Exception as e:
        return _err(e)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def MyQuotationsView(request):
    # Leads received by the logged-in seller's business.
    try:
        try:
            limit = int(request.GET.get("limit", 50))
        except (ValueError, TypeError):
            limit = 50
        limit = max(1, min(limit, 200))
        return _ok(GC.my_quotations(request.user, limit=limit))
    except Exception as e:
        return _err(e)


@api_view(["GET"])
@permission_classes([AllowAny])
def PlanTemplatesView(request):
    # Public Subscription catalogue (optionally ?entityType=) — each row carries
    # `key` (=Subscription.tag) so the v3 checkout resolves a card to a real plan id.
    try:
        return _ok(GC.plan_templates(request.GET.get("entityType", "")))
    except Exception as e:
        return _err(e)


@api_view(["GET"])
@permission_classes([AllowAny])
def ServerTimeView(request):
    # Backend-authoritative clock (Prompt 12): server now + login-time anchor.
    try:
        user = request.user if getattr(request.user, "is_authenticated", False) else None
        return _ok(GC.server_time(user))
    except Exception as e:
        return _err(e)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def PaymentRecheckView(request):
    # Manual single-transaction re-verify (Prompt 10): re-runs CheckPaymentStatus for
    # ONE transaction and returns just that payment's card so a single card refreshes.
    from asgiref.sync import async_to_sync
    from app_ib.Controllers.PaymentGateway.PaymentGatewayController import PaymentGatewayController
    try:
        txn = request.data.get("transactionId")
        if not txn:
            return _bad("transactionId required")
        async_to_sync(PaymentGatewayController.CheckPaymentStatus)(txn, {})
        return _ok(GC.payment_card(request.user, txn))
    except Exception as e:
        return _err(e)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ManualPlanView(request):
    # Manual (offline) plan purchase: the buyer pays by bank/UPI transfer and submits
    # their transaction id. Creates the chosen entity plan INACTIVE (pending backend
    # verification) and flips the buyer to a seller immediately so they can open the
    # seller dashboard. Returns the freshly-created (pending) plan card.
    try:
        plan_id = request.data.get("planId")
        txn = request.data.get("transactionId")
        if not plan_id:
            return _bad("planId required")
        if not txn:
            return _bad("transactionId required")
        return _ok(GC.create_manual_plan(request.user, plan_id, txn))
    except Exception as e:
        return _err(e)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def UpgradePreviewView(request):
    # Validate an upgrade + return the prorated settlement (Prompt 9). Always 200;
    # read data.allowed / data.settleAmount / data.reason on the client.
    from asgiref.sync import async_to_sync
    from app_ib.Controllers.Plans.PlanController import PLAN_CONTROLLER
    try:
        resp = async_to_sync(PLAN_CONTROLLER.PreviewUpgrade)(
            request.user, request.data.get("entityType"), request.data.get("targetPlanId"))
        return _ok(resp.data, resp.message)
    except Exception as e:
        return _err(e)


# ==========================================================================
# 8c. Entity resolve (public, AllowAny)
# ==========================================================================
@api_view(["GET"])
@permission_classes([AllowAny])
def ResolveEntityView(request, entityType, slug):
    try:
        return _ok(GC.resolve_entity(entityType, slug))
    except Exception as e:
        return _err(e)


# ==========================================================================
# 9. Video CRUD
# ==========================================================================
@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def VideoListCreateView(request, entityType, objectId):
    if entityType not in ENTITY_TYPE.ALL:
        return _bad("unsupported entityType")
    if request.method == "POST":
        if not request.user or not request.user.is_authenticated:
            return ServerResponse(response=False, code=RESPONSE_CODES.auth_error,
                                  message="authentication required", data={})
        try:
            return _ok(GC.create_video(request.user, entityType, objectId, request.data),
                       "Video created")
        except Exception as e:
            return _err(e)
    try:
        return _ok(GC.list_videos(entityType, objectId))
    except Exception as e:
        return _err(e)


@api_view(["PUT", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def VideoUpdateDeleteView(request, videoId):
    try:
        if request.method == "DELETE":
            GC.delete_video(request.user, videoId)
            return _ok({}, "Video deleted")
        return _ok(GC.update_video(request.user, videoId, request.data), "Video updated")
    except Exception as e:
        return _err(e)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def VideoSetPrimaryView(request, videoId):
    try:
        return _ok(GC.set_primary_video(request.user, videoId), "Set as primary")
    except Exception as e:
        return _err(e)


# ==========================================================================
# 10. Leads
# ==========================================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def LeadsPrioritizedView(request):
    business_id = request.GET.get("businessId")
    if business_id:
        try:
            business_id = int(business_id)
        except (ValueError, TypeError):
            return _bad("businessId must be an integer")
    try:
        return _ok(GC.prioritized_leads(request.user, business_id))
    except Exception as e:
        return _err(e)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def LeadAcceptView(request, leadId):
    try:
        return _ok(GC.accept_lead(request.user, leadId))
    except Exception as e:
        return _err(e)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def LeadDeclineView(request, leadId):
    reason = (request.data or {}).get("reason", "")
    try:
        return _ok(GC.decline_lead(request.user, leadId, reason))
    except Exception as e:
        return _err(e)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def LeadCreateView(request):
    """Buyer-facing enquiry/lead create — universal connect wizard."""
    if not request.data.get("intent"):
        return _bad("intent required")
    try:
        return _ok(GC.create_lead(request.user, request.data), "Lead created")
    except Exception as e:
        return _err(e)


# ==========================================================================
# 11. Platform ads
# ==========================================================================
@api_view(["GET"])
@permission_classes([AllowAny])
def AdsListView(request):
    page_slug = request.GET.get("page", "")
    placement = request.GET.get("placement", "")
    try:
        return _ok(GC.get_ads(page_slug, placement))
    except Exception as e:
        return _err(e)


@api_view(["POST"])
@permission_classes([AllowAny])
def AdClickView(request, adId):
    try:
        return _ok(GC.click_ad(adId))
    except Exception as e:
        return _err(e)


# ==========================================================================
# 16. Credential CRUD — Award + ProcessStep + Expertise (Phase 1)
# ==========================================================================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def AwardCreateView(request):
    """POST /engine/credentials/award/ — create an Award row for an owned entity."""
    try:
        return _ok(GC.create_award(request.user, request.data), "Award created")
    except ValueError as e:
        return _bad(str(e))
    except Exception as e:
        return _err(e)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def AwardUpdateDeleteView(request, awardId):
    """PATCH /engine/credentials/award/<awardId>/ — partial update.
    DELETE /engine/credentials/award/<awardId>/ — soft delete (isActive=False)."""
    try:
        if request.method == "DELETE":
            GC.delete_award(request.user, awardId)
            return _ok({}, "Award deleted")
        return _ok(GC.update_award(request.user, awardId, request.data), "Award updated")
    except Exception as e:
        return _err(e)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ProcessStepCreateView(request):
    """POST /engine/credentials/process-step/ — create a ProcessStep for an owned entity."""
    try:
        return _ok(GC.create_process_step(request.user, request.data), "Process step created")
    except ValueError as e:
        return _bad(str(e))
    except Exception as e:
        return _err(e)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
def ProcessStepUpdateDeleteView(request, stepId):
    """PATCH /engine/credentials/process-step/<stepId>/ — partial update.
    DELETE /engine/credentials/process-step/<stepId>/ — soft delete."""
    try:
        if request.method == "DELETE":
            GC.delete_process_step(request.user, stepId)
            return _ok({}, "Process step deleted")
        return _ok(GC.update_process_step(request.user, stepId, request.data), "Process step updated")
    except Exception as e:
        return _err(e)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def ExpertiseSetView(request):
    """PUT /engine/credentials/expertise/ — set the entity's expertiseTags.
    Body: {entityType, entityId, tags: [string, ...]}."""
    try:
        return _ok(GC.set_expertise(request.user, request.data), "Expertise updated")
    except ValueError as e:
        return _bad(str(e))
    except Exception as e:
        return _err(e)


# ==========================================================================
# 17. Recently-viewed summary
# ==========================================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def RecentlyViewedSummaryView(request):
    """GET /engine/recently-viewed/summary/ — facets, KPIs, continue banner."""
    try:
        return _ok(GC.recently_viewed_summary(request.user))
    except Exception as e:
        return _err(e)


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
def MySessionsView(request):
    """GET /engine/my/sessions/
    Returns active sessions for the authenticated user.
    Marks the session matching the caller's access token as isCurrent.
    """
    current_jti = _get_sjti_from_token(request)
    try:
        return _ok(GC.my_sessions(request.user, current_jti=current_jti or None))
    except Exception as e:
        return _err(e)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def RevokeSessionView(request, sessionId):
    """POST /engine/my/sessions/<sessionId>/revoke/
    Revoke a single active session owned by the authenticated user.
    Also blacklists the associated refresh token (best-effort).
    """
    try:
        return _ok(GC.revoke_session(request.user, sessionId))
    except Exception as e:
        return _err(e)


# ==========================================================================
# 12. SSE ?token= auth — patched UserStreamView
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
def RelatedItemsView(request, entityType, objectId):
    try:
        limit = int(request.GET.get("limit", 12))
    except (ValueError, TypeError):
        limit = 12
    limit = max(1, min(limit, 50))
    try:
        return _ok(GC.related_items(entityType, objectId, limit))
    except Exception as e:
        return _err(e)


# ==========================================================================
# Phase 3 — 2. Newsletter subscribe
# ==========================================================================
@api_view(["POST"])
@permission_classes([AllowAny])
def NewsletterSubscribeView(request):
    email = (request.data.get("email") or "").strip()
    if not email:
        return _bad("email is required")
    source = request.data.get("source", "blog")
    user = request.user if request.user and request.user.is_authenticated else None
    try:
        return _ok(GC.newsletter_subscribe(email, source, user))
    except ValueError as e:
        return _bad(str(e))
    except Exception as e:
        return _err(e)


# ==========================================================================
# Phase 3 — 3. Blog featured
# ==========================================================================
@api_view(["GET"])
@permission_classes([AllowAny])
def FeaturedBlogsView(request):
    try:
        limit = int(request.GET.get("limit", 1))
    except (ValueError, TypeError):
        limit = 1
    limit = max(1, min(limit, 20))
    try:
        return _ok(GC.featured_blogs(limit))
    except Exception as e:
        return _err(e)


# ==========================================================================
# Phase 3 — 4. Catalogue trending
# ==========================================================================
@api_view(["GET"])
@permission_classes([AllowAny])
def TrendingCataloguesView(request):
    period = request.GET.get("period", "")
    city = request.GET.get("city", "")
    try:
        limit = int(request.GET.get("limit", 12))
    except (ValueError, TypeError):
        limit = 12
    try:
        return _ok(GC.trending_catalogues(period, city, limit))
    except Exception as e:
        return _err(e)


# ==========================================================================
# Phase 3 — 5. Engine my/profile/
# ==========================================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def MyProfileView(request):
    try:
        return _ok(GC.my_profile(request.user))
    except Exception as e:
        return _err(e)


# ==========================================================================
# my/change-password/ — authenticated password change (v3 dashboard security)
# ==========================================================================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def ChangePasswordView(request):
    """POST /engine/my/change-password/
    Body: { currentPassword, newPassword, confirmPassword }
    Verifies the current password then updates it. v3-only.
    """
    try:
        return _ok(GC.change_password(request.user, request.data), "Password updated")
    except ValueError as e:
        return _bad(str(e))
    except Exception as e:
        return _err(e)
