"""Thin views for the remaining v3 admin ops modules (promptsadmin tasks
20/24/25/27/29/30/32/34/35/36). Each delegates to its controller; admin-gated."""
from adrf.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.decorators.ViewDecorator import exceptionHandler

from interior_admin.Validators.adminValidators import hasAccess
from interior_admin.Controllers.Subs.SubsController import SUBS_CONTROLLER
from interior_admin.Controllers.Leads.LeadsController import LEADS_CONTROLLER
from interior_admin.Controllers.WebAnalytics.WebAnalyticsController import WEB_ANALYTICS_CONTROLLER
from interior_admin.Controllers.Reviews.ReviewsController import REVIEWS_CONTROLLER
from interior_admin.Controllers.Taxonomy.TaxonomyController import TAXONOMY_CONTROLLER
from interior_admin.Controllers.Feedback.FeedbackController import FEEDBACK_CONTROLLER
from interior_admin.Controllers.PlanRequests.PlanRequestsController import PLAN_REQUESTS_CONTROLLER
from interior_admin.Controllers.Content.ContentController import CONTENT_CONTROLLER


def _int(v, d):
    try: return int(v)
    except (TypeError, ValueError): return d


def gated(fn):
    fn = exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)(fn)
    return fn


# ── subs (task 20) ──
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@gated
async def SubsView(request: Request):
    await hasAccess(request=request)
    return await SUBS_CONTROLLER.List(status=request.query_params.get('status') or None)


# ── routing (task 24) ──
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@gated
async def RoutingView(request: Request):
    await hasAccess(request=request)
    q = request.query_params
    return await LEADS_CONTROLLER.List(status=q.get('status') or None, pageNo=_int(q.get('pageNo'), 1), pageSize=_int(q.get('pageSize'), 20))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@gated
async def RoutingActionView(request: Request, leadId: int):
    await hasAccess(request=request)
    status = (request.data or {}).get('status', 'flagged')
    return await LEADS_CONTROLLER.SetStatus(leadId=leadId, status=status, moduleKey='routing', actor=request.user)


# ── quarantine (task 25) ──
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@gated
async def QuarantineView(request: Request):
    await hasAccess(request=request)
    q = request.query_params
    return await LEADS_CONTROLLER.List(status=q.get('status') or 'quarantine', pageNo=_int(q.get('pageNo'), 1), pageSize=_int(q.get('pageSize'), 20))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@gated
async def QuarantineActionView(request: Request, leadId: int):
    await hasAccess(request=request)
    status = (request.data or {}).get('status', 'released')
    return await LEADS_CONTROLLER.SetStatus(leadId=leadId, status=status, moduleKey='quarantine', actor=request.user)


# ── web analytics (task 27) ──
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@gated
async def WebAnalyticsView(request: Request):
    await hasAccess(request=request)
    return await WEB_ANALYTICS_CONTROLLER.Get()


# ── reviews (task 30) ──
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@gated
async def ReviewsView(request: Request):
    await hasAccess(request=request)
    q = request.query_params
    return await REVIEWS_CONTROLLER.List(pageNo=_int(q.get('pageNo'), 1), pageSize=_int(q.get('pageSize'), 20))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@gated
async def ReviewHideView(request: Request, reviewId: int):
    await hasAccess(request=request)
    return await REVIEWS_CONTROLLER.Hide(reviewId=reviewId, actor=request.user)


# ── cat-region taxonomy (task 32) ──
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@gated
async def TaxonomyView(request: Request):
    await hasAccess(request=request)
    if request.method == 'POST':
        d = request.data or {}
        return await TAXONOMY_CONTROLLER.AddCategory(value=d.get('value', ''), label=d.get('label', ''), actor=request.user)
    return await TAXONOMY_CONTROLLER.List()


# ── feedback (task 34) ──
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@gated
async def FeedbackView(request: Request):
    await hasAccess(request=request)
    q = request.query_params
    return await FEEDBACK_CONTROLLER.List(status=q.get('status') or None, pageNo=_int(q.get('pageNo'), 1), pageSize=_int(q.get('pageSize'), 20))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@gated
async def FeedbackStatusView(request: Request, feedbackId: int):
    await hasAccess(request=request)
    return await FEEDBACK_CONTROLLER.SetStatus(feedbackId=feedbackId, status=(request.data or {}).get('status', 'viewed'))


# ── plan-requests (task 35) ──
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@gated
async def PlanRequestsView(request: Request):
    await hasAccess(request=request)
    q = request.query_params
    return await PLAN_REQUESTS_CONTROLLER.List(stage=q.get('stage') or None, pageNo=_int(q.get('pageNo'), 1), pageSize=_int(q.get('pageSize'), 20))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@gated
async def PlanRequestStageView(request: Request, requestId: int):
    await hasAccess(request=request)
    return await PLAN_REQUESTS_CONTROLLER.SetStage(requestId=requestId, stage=(request.data or {}).get('stage', ''), actor=request.user)


# ── content / blog (task 36) ──
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@gated
async def ContentView(request: Request):
    await hasAccess(request=request)
    q = request.query_params
    return await CONTENT_CONTROLLER.List(pageNo=_int(q.get('pageNo'), 1), pageSize=_int(q.get('pageSize'), 20))


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@gated
async def ContentFeatureView(request: Request, blogId: int):
    await hasAccess(request=request)
    return await CONTENT_CONTROLLER.ToggleFeatured(blogId=blogId, actor=request.user)
