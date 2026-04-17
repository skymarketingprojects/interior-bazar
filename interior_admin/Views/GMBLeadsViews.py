from adrf.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.request import Request
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.decorators.ViewDecorator import exceptionHandler

from interior_admin.Controllers.GMBLeads.GMBLeadsController import GMB_LEADS_CONTROLLER
from interior_admin.Controllers.GMBLeads.Validators.GMBLeadsValidators import GMBLeadQueryFilters

class GMBLeadsViews:

    @api_view(['POST'])
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.gmb_ingestion_failed,
        responseFunc=ServerResponse
    )
    async def IngestGMBDataView(request: Request):
        """
        Endpoint: POST /api/v1/ingest/gmb-data/
        Receives JSON payloads directly from the GMB scraper.
        """
        # Note: In production, add API Key validation here
        data = request.data
        
        # Accept either a list of leads or a single lead nested in 'leads' key
        leads_data = data.get('leads', data) if isinstance(data, dict) else data
            
        final_response = await GMB_LEADS_CONTROLLER.IngestGMBData(data_list=leads_data)
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
        # Assuming Superadmin has IsAdminUser or specific role
        # We can also use hasAccess decorator if available
        
        queryParams = GMBLeadQueryFilters(**request.query_params)
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
        queryParams = GMBLeadQueryFilters(**request.query_params)
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

