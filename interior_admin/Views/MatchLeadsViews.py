from adrf.decorators import api_view
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES,ACCESSLIST
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from interior_admin.Controllers.MatchLeads.MatchLeadsController import MATCH_LEADS_CONTROLLER
from interior_admin.Validators.adminValidators import hasAccess
@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def MatchLeadsView(request):
    try:
        userIns = request.user
        await hasAccess(request=request)
        queryId = request.query_params.get(NAMES.QUERY_ID)
        result = await MATCH_LEADS_CONTROLLER.GetBusinessCandidates(userIns=userIns,queryId=queryId)
        return ServerResponse(
            response=result.response,
            message=result.message,
            data=result.data,
            code=result.code
        )
    except Exception as e:
        pass
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.error,
            code=RESPONSE_CODES.error,
            data={}
        )
