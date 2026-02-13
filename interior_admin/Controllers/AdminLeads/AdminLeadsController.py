from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler

from .Validators.AdminLeadsValidators import AdminLeadQueryFilters
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.models import LeadQuery,Business
from app_ib.Controllers.Query.Tasks.QueryTasks import LEAD_QUERY_TASK

from .Tasks.AdminLeadsTasks import ADMIN_LEADS_TASKS
from interior_admin.Controllers.AdminLeads.Validators.AdminLeadsValidators import AdminLeadsCreateSchema,AdminLeadsUpdateSchema
from interior_admin.Validators.adminValidators import hasAccess
from django.db.models import Q
from django.core.paginator import Paginator
import asyncio

class ADMIN_LEADS_CONTROLLER:
    @classmethod
    async def GetQueries(self,user_ins,pageNo=1,size=10):
        try:

            # Step 2: Get blog data
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

class ADMIN_LEADS_CONTROLLER_V2:
    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.query_fetch_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.query_fetch_success
    )
    async def GetQueries(self,queryParams:AdminLeadQueryFilters):
        lead_query= None
        filters = Q()

        # Assigned / Unassigned (business FK presence)
        if queryParams.assigned is not None:
            if queryParams.assigned:
                filters &= Q(business__isnull=False)
            else:
                filters &= Q(business__isnull=True)

        # Lead Status (TextField single value)
        if queryParams.leadStatus:
            filters &= Q(leadStatus__iexact=queryParams.leadStatus)

        # Time range (independent safe bounds)
        if queryParams.timeFrom:
            filters &= Q(timestamp__gte=queryParams.timeFrom)

        if queryParams.timeTo:
            filters &= Q(timestamp__lte=queryParams.timeTo)

        # Tags (model = TextField single, not relation)
        if queryParams.tags:
            filters &= Q(tag__in=queryParams.tags)

        # Stages (model = single TextField)
        if queryParams.stages:
            filters &= Q(stage__in=queryParams.stages)

            
        lead_query = await sync_to_async(
            lambda: LeadQuery.objects.filter(filters).order_by('-timestamp')
        )()

        paginator = Paginator(lead_query, queryParams.pageSize)
        page_obj = paginator.get_page(queryParams.pageNo)

        # Step 3: Gather blog data concurrently
        tasks = [ADMIN_LEADS_TASKS.GetLeadQueryTask(leads) for leads in page_obj]
        leads_details = await asyncio.gather(*tasks)

        # Step 4: Build and return plain dict response
        blog_data = {
            "leads": leads_details,
                "current_page": page_obj.number,
                "hasNext": page_obj.has_next(),
                "hasPrevious": page_obj.has_previous(),
                "totalPages": paginator.num_pages,
                "totalCount": len(lead_query),
                "pageSize": queryParams.pageSize
        }

        return True,blog_data
    
    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.funnel_query_create_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.funnel_query_created_success
    )
    async def createQuery(self,data:AdminLeadsCreateSchema):
        data = await LEAD_QUERY_TASK.CreateLeadQueryTask(data=data)
        return data
    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.query_update_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.query_update_success
    )
    async def updateQuery(self,data:AdminLeadsUpdateSchema,leadId:int):
        lead = await sync_to_async(LeadQuery.objects.get)(pk=leadId)
        data = await LEAD_QUERY_TASK.UpdateLeadQueryTask(data=data,lead_query_ins=lead)
        if data:
            return True,data
        return False,data
    
    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.query_remove_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.query_remove_success
    )
    async def deleteQuery(self,leadId):
        lead = await sync_to_async(LeadQuery.objects.get)(pk=leadId)
        data = await LEAD_QUERY_TASK.DeleteLeadQueryTask(lead_query_ins=lead)
        if data:
            return True,data
        return False,data


    @classmethod
    async def AssignLeadQuery(self,leadId,businessId,user_ins):
        try:
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
