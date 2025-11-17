from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse

from .Tasks.AdminLeadsTasks import ADMIN_LEADS_TASKS
from .Validators.AdminLeadsValidators import ADMIN_LEADS_VALIDATORS
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.models import LeadQuery,Business
from app_ib.Controllers.Query.Tasks.QueryTasks import LEAD_QUERY_TASK

from django.core.paginator import Paginator
import asyncio

class ADMIN_LEADS_CONTROLLER:
    @classmethod
    async def GetQueries(self,user_ins,pageNo=1,size=10):
        try:
            isAdmin = await ADMIN_LEADS_VALIDATORS.IsAdmin(user_ins)
            if not isAdmin:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.unauthorized,
                    code=RESPONSE_CODES.error,
                    data={})
            lead_query= None
            lead_query = await sync_to_async(
                lambda: LeadQuery.objects.all().order_by('-timestamp')
            )()

            paginator = Paginator(lead_query, size)
            page_obj = paginator.get_page(pageNo)

            # Step 3: Gather blog data concurrently
            tasks = [LEAD_QUERY_TASK.GetLeadQueryTask(leads) for leads in page_obj]
            leads_details = await asyncio.gather(*tasks)

            # Step 4: Build and return plain dict response
            blog_data = {
                "leads": leads_details,
                    "current_page": page_obj.number,
                    "hasNext": page_obj.has_next(),
                    "hasPrevious": page_obj.has_previous(),
                    "totalPages": paginator.num_pages,
                    "totalCount": len(lead_query),
                    "pageSize": size
            }

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.query_fetch_success,
                code=RESPONSE_CODES.success,
                data=blog_data)

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.query_fetch_error,
                code=RESPONSE_CODES.error,
                data={
                    'error': str(e)
                })
        
    @classmethod
    async def AssignLeadQuery(self,leadId,businessId,user_ins):
        try:
            isAdmin = await ADMIN_LEADS_VALIDATORS.IsAdmin(user_ins)
            if not isAdmin:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.unauthorized,
                    code=RESPONSE_CODES.error,
                    data={})
            isBusinessExist = await sync_to_async(Business.objects.filter(pk=businessId).exists)()
            isleadExist = await sync_to_async(LeadQuery.objects.filter(pk=leadId).exists)()
            if isBusinessExist and isleadExist:
                businessIns = await sync_to_async(Business.objects.get)(pk=businessId)
                leadIns = await sync_to_async(LeadQuery.objects.get)(pk=leadId)
                assignResult = await LEAD_QUERY_TASK.AssignLeadQueryTask(leadQueryIns=leadIns,business=businessIns)
                # await MY_METHODS.printStatus(f"assigned {assignResult}")
                if assignResult:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.query_assigned_success,
                        code=RESPONSE_CODES.success,
                        data=assignResult)
                return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.query_assigned_faliure,
                        code=RESPONSE_CODES.error,
                        data=assignResult)
            
            data = ''
            if not isBusinessExist and not isleadExist:
                data = "business and lead does not exist"
            elif not isBusinessExist:
                data = "business not exist"
            elif not isleadExist:
                data = "lead query not exist"
            return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.query_assigned_faliure,
                        code=RESPONSE_CODES.error,
                        data={"error":data})
        except Exception as e:
            # await MY_METHODS.printStatus(f'fetch quries error {e}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.query_assigned_faliure,
                code=RESPONSE_CODES.error,
                data={
                    'error': str(e)
                })
