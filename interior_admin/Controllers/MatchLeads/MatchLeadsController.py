from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse

from .Tasks.MatchLeadsTasks import MATCH_LEADS_TASKS
from .Validators.MatchLeadsValidators import MATCH_LEADS_VALIDATORS

from app_ib.models import LeadQuery
from app_ib.Utils.MyMethods import MY_METHODS


class MATCH_LEADS_CONTROLLER:
    @classmethod
    async def GetBusinessCandidates(cls, userIns, queryId):
        try:
            # Optional admin check
            # if userIns.type != 'admin':
            #     return LocalResponse(
            #         response=RESPONSE_MESSAGES.error,
            #         message=RESPONSE_MESSAGES.unauthorized,
            #         code=RESPONSE_CODES.error,
            #         data={}
            #     )

            # Fetch single lead by ID
            lead_query = await sync_to_async(
                lambda: LeadQuery.objects.filter(pk=queryId).first()
            )()

            if not lead_query:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message="Lead query not found",
                    code=RESPONSE_CODES.error,
                    data={}
                )

            # Run match task for this lead only
            leadData = await MATCH_LEADS_TASKS.MatchLeadTask(lead_query)
            #await MY_METHODS.printStatus(f'leadData {leadData}')

            if leadData is None:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message="No matching businesses found",
                    code=RESPONSE_CODES.error,
                    data={}
                )

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message="Business candidates fetched successfully",
                code=RESPONSE_CODES.success,
                data={"lead_candidates": leadData}
            )

        except Exception as e:
            await MY_METHODS.printStatus(f"Error in GetBusinessCandidates: {e}")
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Error while fetching candidates",
                code=RESPONSE_CODES.error,
                data={"error": str(e)}
            )
