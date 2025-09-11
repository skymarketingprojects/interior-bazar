import asyncio
from app_ib.Utils.MyMethods import MY_METHODS
from django.http import JsonResponse
from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from interior_admin.Controllers.AdminPanel.AdminPanelController import ADMIN_PANEL_CONTROLLER

@api_view(['POST'])
async def GetBusinessTilesStatsView(request):
    try:
        # Convert request.data to dot notation object
        data = request.data

        start_date = data.get('start_date', None)
        end_date = data.get('end_date', None)
        page_number = data.get('page_number', 1)  # Default to page 1
        page_size = data.get('page_size', 10)  # Default to 10 items per page

        # Call the controller to get business tiles data
        final_response = await asyncio.gather(
            ADMIN_PANEL_CONTROLLER.GetBusinessTilesStats(
                start_date=start_date,
                end_date=end_date,
                page_number=page_number,
                page_size=page_size
            )
        )
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data
        )

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.business_tile_fetch_error,
            code=RESPONSE_CODES.error,
            data={
                'error': str(e)
            }
        )
@api_view(['GET'])
async def GetAdminDashboardStatsView(request):
    try:
        # No filters needed for this endpoint
        final_response = await asyncio.gather(
            ADMIN_PANEL_CONTROLLER.GetAdminDashboardStats()
        )
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data
        )

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.dashboard_fetch_error,
            code=RESPONSE_CODES.error,
            data={
                'error': str(e)
            }
        )
@api_view(['GET'])
async def GetPlatformLeadsStatsView(request):
    try:
        final_response = await ADMIN_PANEL_CONTROLLER.GetAllLeadsStats()
        # final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data
        )

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.platform_leads_fetch_error,
            code=RESPONSE_CODES.error,
            data={
                'error': str(e)
            }
        )
@api_view(['POST'])
async def GetAssignedLeadsTilesView(request):
    try:
        # Convert request.data to dot notation object
        data = request.data

        start_date = data.get('start_date', None)
        end_date = data.get('end_date', None)
        page_number = data.get('page_number', 1)  # Default to page 1
        page_size = data.get('page_size', 10)  # Default to 10 items per page

        # Call the controller to get assigned leads data (paginated)
        final_response = await asyncio.gather(
            ADMIN_PANEL_CONTROLLER.GetPaginatedLeadsStats(
                start_date=start_date,
                end_date=end_date,
                search_query=None,  # Assigned leads would be filtered by business assignment
                page_number=page_number,
                page_size=page_size
            )
        )
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data
        )

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.assigned_leads_fetch_error,
            code=RESPONSE_CODES.error,
            data={
                'error': str(e)
            }
        )


@api_view(['GET'])
async def GetAllUserBusinessStatsView(request):
    try:
        final_response = await asyncio.gather(
            ADMIN_PANEL_CONTROLLER.GetAllUserBusinessStats()
        )
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data
        )
    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message="Failed to fetch user/business stats.",
            code=RESPONSE_CODES.error,
            data={"error": str(e)}
        )


@api_view(['GET'])
async def GetTodaySignupsStatsView(request):
    try:
        final_response = await asyncio.gather(
            ADMIN_PANEL_CONTROLLER.GetTodaySignupsStats()
        )
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data
        )
    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message="Failed to fetch today signups.",
            code=RESPONSE_CODES.error,
            data={"error": str(e)}
        )


@api_view(['POST'])
async def GetChartsStatsView(request):
    try:
        # No filters needed (filters are handled inside task by daily/weekly/monthly buckets)
        final_response = await asyncio.gather(
            ADMIN_PANEL_CONTROLLER.GetChartsStats()
        )
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data
        )
    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message="Failed to fetch charts.",
            code=RESPONSE_CODES.error,
            data={"error": str(e)}
        )