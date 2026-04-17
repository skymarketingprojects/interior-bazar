from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler

from .Validators.AdminLeadsValidators import AdminLeadQueryFilters
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.models import LeadQuery,Business
from app_ib.Controllers.Query.Tasks.QueryTasks import LEAD_QUERY_TASK
from app_ib.Utils.MyMethods import MY_METHODS

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
    async def GetQueries(cls, queryParams: AdminLeadQueryFilters):
        """
        High performance paginated lead query retrieval.
        Fixes async context issues with Paginator and improves speed via bulk serialization.
        """
        filters = Q()

        # 1. Build filters (keeping existing logic)
        if queryParams.assigned is not None:
            assigned = queryParams.assigned
            if isinstance(assigned, str):
                assigned = str(assigned).lower() in ['true', '1', 'yes']
            
            if assigned:
                filters &= Q(business__isnull=False)
            else:
                filters &= Q(business__isnull=True)

        if queryParams.leadStatus:
            leadStatus = queryParams.leadStatus
            if isinstance(leadStatus, str):
                leadStatus = [s.strip() for s in leadStatus.split(',') if s.strip()]
            
            lead_status_q = Q()
            for s in leadStatus:
                lead_status_q |= Q(leadStatus__icontains=s) | Q(status__icontains=s)
            filters &= lead_status_q

        if queryParams.timeFrom:
            filters &= Q(timestamp__gte=queryParams.timeFrom)

        if queryParams.timeTo:
             filters &= Q(timestamp__lte=queryParams.timeTo)

        if queryParams.tags:
            tags = queryParams.tags
            if isinstance(tags, str):
                tags = [s.strip() for s in tags.split(',') if s.strip()]
            
            tags_q = Q()
            for t in tags:
                tags_q |= Q(tag__icontains=t)
            filters &= tags_q

        if queryParams.stages:
            stages = queryParams.stages
            if isinstance(stages, str):
                stages = [s.strip() for s in stages.split(',') if s.strip()]
            
            stages_q = Q()
            for sg in stages:
                stages_q |= Q(stage__icontains=sg)
            filters &= stages_q

        if queryParams.status:
            status = queryParams.status
            if isinstance(status, str):
                status = [s.strip() for s in status.split(',') if s.strip()]
            
            status_q = Q()
            for st in status:
                status_q |= Q(status__icontains=st) | Q(leadStatus__icontains=st)
            filters &= status_q

        if queryParams.searchText:
            search_filters = Q(
                Q(name__icontains=queryParams.searchText) |
                Q(phone__icontains=queryParams.searchText) |
                Q(email__icontains=queryParams.searchText) |
                Q(city__icontains=queryParams.searchText)
            )
            
            stripped_search_text = queryParams.searchText.strip()
            if stripped_search_text.isdigit():
                search_filters |= Q(pk=int(stripped_search_text))
                
            filters &= search_filters

        if queryParams.category:
            category = queryParams.category
            if isinstance(category, str):
                category = [s.strip() for s in category.split(',') if s.strip()]
            
            category_q = Q()
            for ct in category:
                category_q |= Q(category__icontains=ct)
            filters &= category_q

        # 2. Synchronous Database Operations (Pagination + Selection)
        def get_paginated_queries():
            # Use select_related to avoid N+1 queries during serialization
            queryset = LeadQuery.objects.filter(filters).select_related('business').order_by('-timestamp')
            
            paginator = Paginator(queryset, queryParams.pageSize)
            page_obj = paginator.get_page(queryParams.pageNo)
            
            return {
                "items": list(page_obj), # Force evaluation inside sync_to_async
                "current_page": page_obj.number,
                "hasNext": page_obj.has_next(),
                "hasPrevious": page_obj.has_previous(),
                "totalPages": paginator.num_pages,
                "totalCount": paginator.count
            }

        page_data = await sync_to_async(get_paginated_queries)()

        # 3. Bulk Serialization
        leads_details = await ADMIN_LEADS_TASKS.BulkSerializeLeadQueries(page_data["items"])

        # 4. Final Response Construction
        response_data = {
            "leads": leads_details,
            "current_page": page_data["current_page"],
            "hasNext": page_data["hasNext"],
            "hasPrevious": page_data["hasPrevious"],
            "totalPages": page_data["totalPages"],
            "totalCount": page_data["totalCount"],
            "pageSize": queryParams.pageSize
        }

        return True, response_data
    
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
        await MY_METHODS.printStatus(f'UpdateAdminQueryView data:-{data}')
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
