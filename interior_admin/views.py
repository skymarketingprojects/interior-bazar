import asyncio
from adrf.decorators import api_view

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.Names import NAMES, ACCESSLIST
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.decorators.ViewDecorator import exceptionHandler

from app_ib.Controllers.FunnelQuery.FunnelQueryController import FUNNEL_QUERY_CONTROLLER
from interior_admin.Controllers.AdminPanel.AdminPanelController import ADMIN_PANEL_CONTROLLER, ADMIN_PANEL_CONTROLLER_V2
from .Controllers.AdminPanel.Validators.AdminPanelValidators import UpdatePlanIntent
import asyncio
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from interior_admin.Validators.adminValidators import hasAccess

class AdminPanelViewsV1:

    @api_view(['POST'])
    @permission_classes([IsAuthenticated])
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.business_tile_fetch_error,
        responseFunc=ServerResponse
        )
    async def GetBusinessTilesStatsView(request:Request):
            await hasAccess(request=request)
            # Convert request.data to dot notation object
            data = request.data

            start_date = data.get(NAMES.START_DATE, None)
            end_date = data.get(NAMES.END_DATE, None)
            page_number = data.get(NAMES.PAGE_NUMBER, 1)
            page_size = data.get(NAMES.PAGE_SIZE, 10) 

            # Call the controller to get business tiles data
            final_response = await ADMIN_PANEL_CONTROLLER.GetBusinessTilesStats(
                    start_date=start_date,
                    end_date=end_date,
                    page_number=page_number,
                    page_size=page_size
                )

            return final_response

    @api_view(['GET'])
    @permission_classes([IsAuthenticated])
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.dashboard_fetch_error,
        responseFunc=ServerResponse
    )
    async def GetAdminDashboardStatsView(request):
        await hasAccess(request=request)
        
        final_response = await ADMIN_PANEL_CONTROLLER.GetAdminDashboardStats()

        return final_response


    @api_view(['GET'])
    @permission_classes([IsAuthenticated])
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.platform_leads_fetch_error,
        responseFunc=ServerResponse
    )
    async def GetPlatformLeadsStatsView(request):
        await hasAccess(request=request)
        
        final_response = await ADMIN_PANEL_CONTROLLER.GetAllLeadsStats()

        return final_response
    @api_view(['POST'])
    @permission_classes([IsAuthenticated])
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.assigned_leads_fetch_error,
        responseFunc=ServerResponse
    )
    async def GetAssignedLeadsTilesView(request):
        await hasAccess(request=request)
        
        data = request.data

        start_date = data.get(NAMES.START_DATE, None)
        end_date = data.get(NAMES.END_DATE, None)
        page_number = data.get(NAMES.PAGE_NUMBER, 1)  # Default to page 1
        page_size = data.get(NAMES.PAGE_SIZE, 10)  # Default to 10 items per page

        # Call the controller to get assigned leads data (paginated)
        final_response = await ADMIN_PANEL_CONTROLLER.GetPaginatedLeadsStats(
                start_date=start_date,
                end_date=end_date,
                search_query=None,  # Assigned leads would be filtered by business assignment
                page_number=page_number,
                page_size=page_size
            )

        return final_response

    @api_view(['GET'])
    @permission_classes([IsAuthenticated])
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.dashboard_fetch_error,
        responseFunc=ServerResponse
    )
    async def GetDashboardDataView(request):
        await hasAccess(request=request)

        await MY_METHODS.printStatus("GetDashboardDataView")
        
        final_response = await ADMIN_PANEL_CONTROLLER.GetDashboardData()
        await MY_METHODS.printStatus("resp",final_response)

        return final_response
    
    @api_view(['GET'])
    @permission_classes([IsAuthenticated])
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.dashboard_fetch_error,
        responseFunc=ServerResponse
    )
    async def GetAllUserBusinessStatsView(request):
        await hasAccess(request=request)
        
        final_response = await ADMIN_PANEL_CONTROLLER.GetAllUserBusinessStats()

        return final_response
        

    @api_view(['GET'])
    @permission_classes([IsAuthenticated])
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.dashboard_fetch_error,
        responseFunc=ServerResponse
    )
    async def GetDailyUsersStatsView(request):
        await hasAccess(request=request)
        final_response = await ADMIN_PANEL_CONTROLLER.GetDailyUserData()
            
        return final_response

    @api_view(['GET'])
    @permission_classes([IsAuthenticated])
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.dashboard_fetch_error,
        responseFunc=ServerResponse
    )
    async def GetTodaySignupsStatsView(request):
        await hasAccess(request=request)
        
        final_response = await ADMIN_PANEL_CONTROLLER.GetTodaySignupsStats()

        return final_response


    @api_view(['GET'])
    @permission_classes([IsAuthenticated])
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.dashboard_fetch_error,
        responseFunc=ServerResponse
    )
    async def GetChartsStatsView(request):
        await hasAccess(request=request)
            
        final_response = await ADMIN_PANEL_CONTROLLER.GetChartsStats()

        return final_response
        
    @api_view(['GET'])
    @permission_classes([IsAuthenticated])
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.query_fetch_error,
        responseFunc=ServerResponse
    )
    async def GetFunnelQueriesView(request,pageNumber, pageSize):
        await hasAccess(request=request)
        final_response = await FUNNEL_QUERY_CONTROLLER.GetFunnelQueries(pageNumber=pageNumber, pageSize=pageSize)

        return final_response

    @api_view(['GET'])
    @permission_classes([IsAuthenticated])
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.query_fetch_error,
        responseFunc=ServerResponse
    )
    async def GetTotalUsersView(request):
        await hasAccess(request=request)
        final_response = await ADMIN_PANEL_CONTROLLER.GetTotalNoOfUsers()

        return final_response

class AdminPanelViewsV2:

    @api_view(['POST'])
    @permission_classes([IsAuthenticated])
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.business_tile_fetch_error,
        responseFunc=ServerResponse
        )
    async def GetBusinessTilesStatsView(request: Request):
            await hasAccess(request=request)
            # Convert request.data to dot notation object
            data = request.data

            start_date = data.get(NAMES.START_DATE, None)
            end_date = data.get(NAMES.END_DATE, None)
            page_number = data.get(NAMES.PAGE_NUMBER, 1)
            page_size = data.get(NAMES.PAGE_SIZE, 10)
            plan = data.get(NAMES.PLAN, None)

            # Call the controller to get business tiles data
            final_response = await ADMIN_PANEL_CONTROLLER_V2.GetBusinessTilesStats(
                    start_date=start_date,
                    end_date=end_date,
                    page_number=page_number,
                    page_size=page_size,
                    plan=plan
                )

            return final_response

    @api_view(['GET'])
    @permission_classes([IsAuthenticated])
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.dashboard_fetch_error,
        responseFunc=ServerResponse
    )
    async def GetAdminDashboardStatsView(request):
        await hasAccess(request=request)
        final_response = await ADMIN_PANEL_CONTROLLER_V2.GetAdminDashboardStats()

        return final_response


    @api_view(['GET'])
    @permission_classes([IsAuthenticated])
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.platform_leads_fetch_error,
        responseFunc=ServerResponse
    )
    async def GetPlatformLeadsStatsView(request):
        await hasAccess(request=request)
        final_response = await ADMIN_PANEL_CONTROLLER_V2.GetAllLeadsStats()

        return final_response
    
    @api_view(['POST'])
    @permission_classes([IsAuthenticated])
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.assigned_leads_fetch_error,
        responseFunc=ServerResponse
    )
    async def GetAssignedLeadsTilesView(request):
        await hasAccess(request=request)
        data = request.data

        start_date = data.get(NAMES.START_DATE, None)
        end_date = data.get(NAMES.END_DATE, None)
        page_number = data.get(NAMES.PAGE_NUMBER, 1)  # Default to page 1
        page_size = data.get(NAMES.PAGE_SIZE, 10)  # Default to 10 items per page

        # Call the controller to get assigned leads data (paginated)
        final_response = await ADMIN_PANEL_CONTROLLER_V2.GetPaginatedLeadsStats(
                start_date=start_date,
                end_date=end_date,
                search_query=None,  # Assigned leads would be filtered by business assignment
                page_number=page_number,
                page_size=page_size
            )

        return final_response

    @api_view(['GET'])
    @permission_classes([IsAuthenticated])
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.dashboard_fetch_error,
        responseFunc=ServerResponse
    )
    async def GetDashboardDataView(request):
        await hasAccess(request=request)
        final_response = await ADMIN_PANEL_CONTROLLER_V2.GetDashboardData()

        return final_response
    
    @api_view(['GET'])
    @permission_classes([IsAuthenticated])
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.dashboard_fetch_error,
        responseFunc=ServerResponse
    )
    async def GetAllUserBusinessStatsView(request):
        await hasAccess(request=request)
        final_response = await ADMIN_PANEL_CONTROLLER_V2.GetAllUserBusinessStats()

        return final_response
        

    @api_view(['GET'])
    @permission_classes([IsAuthenticated])
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.dashboard_fetch_error,
        responseFunc=ServerResponse
    )
    async def GetDailyUsersStatsView(request):
        await hasAccess(request=request)
        final_response = await ADMIN_PANEL_CONTROLLER_V2.GetDailyUserData()
            
        return final_response

    @api_view(['GET'])
    @permission_classes([IsAuthenticated])
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.dashboard_fetch_error,
        responseFunc=ServerResponse
    )
    async def GetTodaySignupsStatsView(request):
        await hasAccess(request=request)
        final_response = await ADMIN_PANEL_CONTROLLER_V2.GetTodaySignupsStats()

        return final_response


    @api_view(['GET'])
    @permission_classes([IsAuthenticated])
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.dashboard_fetch_error,
        responseFunc=ServerResponse
    )
    async def GetChartsStatsView(request):
        await hasAccess(request=request)
            
        final_response = await ADMIN_PANEL_CONTROLLER_V2.GetChartsStats()

        return final_response
        
    @api_view(['GET'])
    @permission_classes([IsAuthenticated])
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.query_fetch_error,
        responseFunc=ServerResponse
    )
    async def GetFunnelQueriesView(request,pageNumber, pageSize):
        await hasAccess(request=request)
        final_response = await FUNNEL_QUERY_CONTROLLER.GetFunnelQueries(pageNumber=pageNumber, pageSize=pageSize)

        return final_response

    @api_view(['GET'])
    @permission_classes([IsAuthenticated])
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.query_fetch_error,
        responseFunc=ServerResponse
    )
    async def GetTotalUsersView(request):
        await hasAccess(request=request)
        final_response = await ADMIN_PANEL_CONTROLLER_V2.GetTotalNoOfUsers()

        return final_response
    @api_view(['GET'])
    @permission_classes([IsAuthenticated])
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.lead_tile_fetch_error,
        responseFunc=ServerResponse
    )
    async def GetLeadAnalyticsView(request):
        await hasAccess(request=request)
        final_response = await ADMIN_PANEL_CONTROLLER_V2.GetLeadAnalyticsStats()

        return final_response

    @api_view(['POST'])
    @permission_classes([IsAuthenticated])
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.plan_intent_update_error,
        responseFunc=ServerResponse
    )
    async def UpdatePlanIntentView(request:Request):
        await hasAccess(request=request)
        data = UpdatePlanIntent(**request.data)
        final_response = await ADMIN_PANEL_CONTROLLER_V2.UpdatePlanIntent(data=data)

        return final_response