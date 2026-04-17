from asgiref.sync import sync_to_async
from django.db.models import Q
import asyncio
from typing import List, Dict, Any, Tuple, Optional

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.Names import NAMES
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES

from interior_admin.models import GMBBusiness
from .Tasks.GMBLeadsTasks import GMB_LEADS_TASKS
from .Validators.GMBLeadsValidators import GMBLeadQueryFilters

class GMBLeadsController:
    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.gmb_ingest_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.gmb_ingest_success
    )
    async def IngestGMBData(cls, data_list: List[Dict[str, Any]]) -> Tuple[bool, Dict[str, Any]]:
        """
        Ingests bulk GMB lead data. 
        """
        # Delegate business logic to IngestGMBDataTask
        data = await GMB_LEADS_TASKS.IngestGMBDataTask(data_list=data_list)
        return True, data

    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.gmb_leads_fetch_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.gmb_leads_fetch_success
    )
    async def GetAllLeads(cls, queryParams: GMBLeadQueryFilters) -> Tuple[bool, Dict[str, Any]]:
        """
        Retrieves all GMB leads with filtering and pagination.
        """
        # Controller collects resources (filters)
        filters = Q()
        if queryParams.platform:
            filters &= Q(platform__icontains=queryParams.platform)
        if queryParams.city:
            filters &= Q(address__icontains=queryParams.city or "")
        if queryParams.zip:
            filters &= Q(address__icontains=queryParams.zip or "")
        
        if queryParams.has_website is not None:
            if queryParams.has_website:
                filters &= Q(web__isnull=False) & ~Q(web='')
            else:
                filters &= Q(web__isnull=True) | Q(web='')
        
        if queryParams.has_social is not None:
            if queryParams.has_social:
                filters &= ~Q(socialLinks=[])
            else:
                filters &= Q(socialLinks=[])
                
        if queryParams.min_rating:
            filters &= Q(ratingValue__gte=queryParams.min_rating)

        sort_field = queryParams.sort_by or NAMES.RANKING_RATE
        if queryParams.order == 'desc':
            sort_field = f'-{sort_field}'
            
        # Delegate main business logic (pagination and search) to Task
        data = await GMB_LEADS_TASKS.PaginateGMBLeadsTask(
            filters_q=filters,
            sort_field=sort_field,
            page_no=queryParams.pageNo,
            page_size=queryParams.pageSize
        )
        return True, data

    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.gmb_my_leads_fetch_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.gmb_my_leads_fetch_success
    )
    async def GetMyLeads(cls, user: Any, queryParams: GMBLeadQueryFilters) -> Tuple[bool, Dict[str, Any]]:
        """
        Retrieves leads assigned to a specific user.
        """
        # Controller collects resources (user-specific filters)
        filters = Q(assignedUser=user)
        if queryParams.platform: filters &= Q(platform__icontains=queryParams.platform)
        if queryParams.city: filters &= Q(address__icontains=queryParams.city or "")
        if queryParams.min_rating: filters &= Q(ratingValue__gte=queryParams.min_rating)

        sort_field = queryParams.sort_by or NAMES.RANKING_RATE
        if queryParams.order == 'desc':
            sort_field = f'-{sort_field}'
            
        # Delegate to Task
        data = await GMB_LEADS_TASKS.PaginateGMBLeadsTask(
            filters_q=filters,
            sort_field=sort_field,
            page_no=queryParams.pageNo,
            page_size=queryParams.pageSize
        )
        return True, data

    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.gmb_assign_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.gmb_assign_success
    )
    async def AssignLead(cls, lead_id: int, user_id: int, trigger_user: Any) -> Tuple[bool, Dict[str, Any]]:
        """
        Collects lead and user instances and delegates assignment to Task.
        """
        # Controller collects instances needed
        lead = await sync_to_async(GMBBusiness.objects.get)(pk=lead_id)
        from app_ib.models import CustomUser
        target_user = await sync_to_async(CustomUser.objects.get)(pk=user_id)
        
        # Delegate main business logic (update and save) to Task
        data = await GMB_LEADS_TASKS.AssignLeadTask(
            lead_ins=lead,
            target_user_ins=target_user,
            trigger_user_ins=trigger_user
        )
        return True, data

GMB_LEADS_CONTROLLER = GMBLeadsController()
