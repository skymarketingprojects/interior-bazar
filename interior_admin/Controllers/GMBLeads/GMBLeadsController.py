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
from .Validators.GMBLeadsValidators import GMBLeadQueryFilters, GMBLeadUpdateSchema
from app_ib.models import CustomUser

from rbac_module.models import Role, Access
class GMBLeadsController:
    # Permission required to be considered part of the "Sales Team" for GMB leads
    SALES_TEAM_PERMISSION = "interior_bazzar:get_my_gmb_leads:get"
    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.gmb_ingest_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.gmb_ingest_success
    )
    async def IngestGMBData(cls, data_list: List[Dict[str, Any]], trigger_user: Any = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Ingests bulk GMB lead data with automated round-robin distribution to available staff.
        """
        assignable_users = await cls._get_assignable_admins_list()
        
        result = await GMB_LEADS_TASKS.IngestGMBDataTask(
            data_list=data_list, 
            trigger_user=trigger_user,
            assignable_users=assignable_users
        )
        return True, result

    @classmethod
    def _build_common_filters(cls, queryParams: GMBLeadQueryFilters) -> Q:
        """
        Builds common Q filters for platform, status, city, rating, etc.
        """
        filters = Q()
        if queryParams.platform:
            filters &= Q(platform__icontains=queryParams.platform)
        if queryParams.status:
            filters &= Q(status__icontains=queryParams.status)
        if queryParams.city:
            filters &= Q(address__icontains=queryParams.city or "")
        if queryParams.state:
            filters &= Q(state__icontains=queryParams.state)
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
            
        return filters

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
        filters = cls._build_common_filters(queryParams)

        sort_field = queryParams.sort_by or NAMES.CREATED_AT
        if queryParams.order == 'desc':
            sort_field = f'-{sort_field}'
            
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
        Retrieves leads assigned to a specific user (Admins see all).
        """
        # Check for full access (Admin bypass)
        # Using sync_to_async for ORM filter call on user roles
        is_admin = await sync_to_async(user.roles.filter(is_full_access=True).exists)()
        
        filters = cls._build_common_filters(queryParams)
        if not is_admin:
            filters &= Q(assignedUser=user)

        sort_field = queryParams.sort_by or NAMES.CREATED_AT
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

    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.gmb_update_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.gmb_update_success
    )
    async def UpdateGMBLead(cls, lead_id: int, data: GMBLeadUpdateSchema, trigger_user: Any) -> Tuple[bool, Dict[str, Any]]:
        """
        Collects lead instance and delegates field updates to Task.
        """
        lead = await sync_to_async(GMBBusiness.objects.get)(pk=lead_id)
        data = await GMB_LEADS_TASKS.UpdateGMBLeadTask(
            lead_ins=lead,
            data=data,
            trigger_user=trigger_user
        )
        return True, data

    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.gmb_create_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.gmb_create_success
    )
    async def CreateSingleLead(cls, data: Dict[str, Any], trigger_user: Any) -> Tuple[bool, Dict[str, Any]]:
        """
        Creates a single GMB lead and assigns it to the creating user.
        """
        data = await GMB_LEADS_TASKS.CreateSingleLeadTask(
            item=data,
            trigger_user=trigger_user
        )
        if not data:
            return False, {}
        return True, data

    @classmethod
    async def _get_assignable_admins_list(cls) -> List[Any]:
        """
        Private helper to get the raw list of assignable Admin instances.
        """
        # Find admins who have a role that contains the GMB view permission
        users_with_access = await sync_to_async(lambda: list(
            CustomUser.objects.filter(
                type=NAMES.ADMIN,
                is_active=True,
                roles__access__permissionName=cls.SALES_TEAM_PERMISSION,
                roles__access__permission=True
            ).exclude(
                roles__is_full_access=True
            ).distinct().order_by('id')
        ))()
        return users_with_access

    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.gmb_leads_fetch_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.success
    )
    async def GetAssignableAdmins(cls) -> Tuple[bool, List[Any]]:
        """
        External API implementation for fetching admins.
        """
        users = await cls._get_assignable_admins_list()
        # Serialize simply for the frontend
        admin_list = [{"id": u.id, "username": u.username, "name": getattr(u, 'name', u.username)} for u in users]
        return True, admin_list

    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.gmb_my_leads_fetch_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.gmb_my_leads_fetch_success
    )
    async def GetUserLeads(cls, userId: int, queryParams: GMBLeadQueryFilters) -> Tuple[bool, Dict[str, Any]]:
        """
        Special endpoint for Superadmins to view leads assigned to a specific userId.
        """
        user_ins = await sync_to_async(CustomUser.objects.get)(id=userId)
        
        filters = cls._build_common_filters(queryParams)
        filters &= Q(assignedUser=user_ins)
        
        data = await GMB_LEADS_TASKS.PaginateGMBLeadsTask(
            filters_q=filters,
            sort_field=queryParams.sort_by,
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
    async def TriggerAutoAssignment(cls, trigger_user: Any) -> Tuple[bool, Dict[str, Any]]:
        """
        Triggers round-robin distribution for all unassigned leads.
        """
        assignable_users = await cls._get_assignable_admins_list()
        data = await GMB_LEADS_TASKS.AutoAssignUnassignedLeadsTask(
            assignable_users=assignable_users,
            trigger_user=trigger_user
        )
        return True, data

GMB_LEADS_CONTROLLER = GMBLeadsController()
