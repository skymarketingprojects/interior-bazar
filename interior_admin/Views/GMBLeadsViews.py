from adrf.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.request import Request
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.decorators.ViewDecorator import exceptionHandler

from interior_admin.Controllers.GMBLeads.GMBLeadsController import GMB_LEADS_CONTROLLER
from interior_admin.Controllers.GMBLeads.Validators.GMBLeadsValidators import GMBLeadQueryFilters, GMBLeadUpdateSchema, GMBLeadCreateSchema
from interior_admin.Validators.adminValidators import hasAccess

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@exceptionHandler(
    errorMessage=RESPONSE_MESSAGES.gmb_ingestion_failed,
    responseFunc=ServerResponse
)
async def IngestGMBDataView(request: Request):
    """
    Endpoint: POST /api/v1/ingest/gmb-data/
    Receives JSON payloads directly from the GMB scraper.
    """
    await hasAccess(request=request)
    data = request.data
    
    # Accept either a list of leads or a single lead nested in 'leads' key
    leads_data = data.get('leads', data) if isinstance(data, dict) else data
        
    final_response = await GMB_LEADS_CONTROLLER.IngestGMBData(data_list=leads_data, trigger_user=request.user)
    return final_response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@exceptionHandler(
    errorMessage=RESPONSE_MESSAGES.gmb_leads_fetch_error,
    responseFunc=ServerResponse
)
async def GetAllLeadsView(request: Request):
    """
    Endpoint: GET /api/v1/admin/all-leads/
    Access: Superadmin only (Checked via IsAdminUser or custom logic).
    """
    await hasAccess(request=request)
    queryParams = GMBLeadQueryFilters(**request.query_params.dict())
    final_response = await GMB_LEADS_CONTROLLER.GetAllLeads(queryParams=queryParams)
    return final_response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@exceptionHandler(
    errorMessage=RESPONSE_MESSAGES.gmb_my_leads_fetch_error,
    responseFunc=ServerResponse
)
async def GetMyLeadsView(request: Request):
    """
    Endpoint: GET /api/v1/leads/my-leads/
    Access: Authenticated Admin Users.
    Returns leads where assigned_user matches the requesting user.
    """
    await hasAccess(request=request)
    queryParams = GMBLeadQueryFilters(**request.query_params.dict())
    final_response = await GMB_LEADS_CONTROLLER.GetMyLeads(user=request.user, queryParams=queryParams)
    return final_response

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@exceptionHandler(
    errorMessage=RESPONSE_MESSAGES.gmb_assign_error,
    responseFunc=ServerResponse
)
async def AssignLeadView(request: Request):
    """
    Assigns a GMB lead to an admin user and logs the activity.
    """
    await hasAccess(request=request)
    lead_id = request.data.get('lead_id')
    user_id = request.data.get('user_id')
    
    if not lead_id or not user_id:
        return ServerResponse(False, RESPONSE_MESSAGES.gmb_missing_ids, code=400)
        
    final_response = await GMB_LEADS_CONTROLLER.AssignLead(
        lead_id=lead_id, 
        user_id=user_id, 
        trigger_user=request.user
    )
    return final_response

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@exceptionHandler(
    errorMessage=RESPONSE_MESSAGES.gmb_update_error,
    responseFunc=ServerResponse
)
async def UpdateGMBLeadView(request: Request, leadId):
    """
    Endpoint: PATCH /api/v1/admin/v1/leads/<leadId>/
    Updates GMB lead fields (remark, status, tier, rankingRate).
    """
    await hasAccess(request=request)
    
    data = GMBLeadUpdateSchema(**request.data)
    final_response = await GMB_LEADS_CONTROLLER.UpdateGMBLead(
        lead_id=leadId,
        data=data,
        trigger_user=request.user
    )
    return final_response

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@exceptionHandler(
    errorMessage=RESPONSE_MESSAGES.gmb_create_error,
    responseFunc=ServerResponse
)
async def CreateSingleLeadView(request: Request):
    """
    Endpoint: POST /api/v1/leads/create/
    Allows frontend users to manually create a single lead.
    The lead is automatically assigned to the request.user.
    """
    await hasAccess(request=request)
    data = GMBLeadCreateSchema(**request.data)
    final_response = await GMB_LEADS_CONTROLLER.CreateSingleLead(data=data.dict(), trigger_user=request.user)
    return final_response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@exceptionHandler(
    errorMessage=RESPONSE_MESSAGES.gmb_leads_fetch_error,
    responseFunc=ServerResponse
)
async def ListGMBAdminsView(request: Request):
    """
    Endpoint: GET /api/v1/admin/v1/admins/
    Returns a list of admins eligible for lead assignment (Sales Team).
    Restricted to Superadmins.
    """
    from rbac_module.models import Role
    if not await Role.objects.filter(users=request.user, is_full_access=True).aexists():
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Access Restricted to Superadmins.")
        
    final_response = await GMB_LEADS_CONTROLLER.GetAssignableAdmins()
    return final_response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@exceptionHandler(
    errorMessage=RESPONSE_MESSAGES.gmb_my_leads_fetch_error,
    responseFunc=ServerResponse
)
async def GetUserLeadsView(request: Request, userId: int):
    """
    Endpoint: GET /api/v1/admin/v1/leads/user/<userId>/
    Allows Superadmins to view leads assigned to a specific staff member.
    """
    from rbac_module.models import Role
    if not await Role.objects.filter(users=request.user, is_full_access=True).aexists():
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Access Restricted to Superadmins.")
        
    queryParams = GMBLeadQueryFilters(**request.query_params.dict())
    final_response = await GMB_LEADS_CONTROLLER.GetUserLeads(userId=userId, queryParams=queryParams)
    return final_response

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@exceptionHandler(
    errorMessage=RESPONSE_MESSAGES.gmb_assign_error,
    responseFunc=ServerResponse
)
async def AutoAssignLeadsView(request: Request):
    """
    Endpoint: POST /api/v1/admin/v1/leads/auto-assign/
    Triggers automated round-robin distribution for all unassigned leads.
    Restricted to Superadmins.
    """
    from rbac_module.models import Role
    if not await Role.objects.filter(users=request.user, is_full_access=True).aexists():
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Access Restricted to Superadmins.")
        
    final_response = await GMB_LEADS_CONTROLLER.TriggerAutoAssignment(trigger_user=request.user)
    return final_response

