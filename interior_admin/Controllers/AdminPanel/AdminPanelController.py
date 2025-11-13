from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from .Tasks.AdminPanelBusinessTasks import ADMIN_PANEL_TASKS
from .Tasks.AdminPanelLeadTasks import LEAD_TASKS
from .Tasks.AdminPannelAnalyticsTask import ANALYTICS_TASKS
import asyncio
from app_ib.models import CustomUser, Business, BusinessPlan
from app_ib.Utils.MyMethods import MY_METHODS
class ADMIN_PANEL_CONTROLLER:

    # Existing Business Methods
    @classmethod
    async def GetBusinessTilesStats(cls, start_date=None, end_date=None, page_number=1, page_size=2):
        try:
            tiles_data = await ADMIN_PANEL_TASKS.GetBusinessTiles(
                start_date=start_date,
                end_date=end_date,
                page_number=page_number,
                page_size=page_size
            )

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message="Business tile data fetched successfully.",
                code=RESPONSE_CODES.success,
                data=tiles_data
            )

        except Exception as e:
            await MY_METHODS.printStatus(f"[Tile Stats Error]: {e}")
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Failed to fetch business tile data.",
                code=RESPONSE_CODES.error,
                data={"error": str(e)}
            )

    # Dashboard Stats
    @classmethod
    async def GetAdminDashboardStats(cls):
        """
        Returns full dashboard stats with totals and all tile data (no filters).
        """
        try:
            (
                total_businesses,
                total_active,
                total_inactive,
                weekly_signups,
                all_tiles
            ) = await asyncio.gather(
                ADMIN_PANEL_TASKS.GetTotalBusinesses(),
                ADMIN_PANEL_TASKS.GetTotalActiveBusinesses(),
                ADMIN_PANEL_TASKS.GetTotalInactiveBusinesses(),
                ADMIN_PANEL_TASKS.GetWeeklySignups(),
                ADMIN_PANEL_TASKS.GetBusinessTiles()  # No filters, will fetch all tiles
            )

            dashboard_data = {
                "totalBusinesses": total_businesses,
                "totalActiveBusinesses": total_active,
                "totalInactiveBusinesses": total_inactive,
                "weeklySignups": weekly_signups,
                "businessTiles": all_tiles
            }

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message="Admin dashboard stats fetched successfully.",
                code=RESPONSE_CODES.success,
                data=dashboard_data
            )

        except Exception as e:
            await MY_METHODS.printStatus(f"[Dashboard Stats Error]: {e}")
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Failed to fetch admin dashboard stats.",
                code=RESPONSE_CODES.error,
                data={"error": str(e)}
            )

    # New: Get All Leads (without pagination)
    @classmethod
    async def GetAllLeadsStats(cls, start_date=None, end_date=None, search_query=None):
        """
        Get all lead statistics (total platform leads, assigned leads, total leads, today's leads, and lead tiles).
        """
        try:
            # Use asyncio.gather to run tasks concurrently
            results = await asyncio.gather(
                LEAD_TASKS.GetTotalUnassignedLeads(),
                LEAD_TASKS.GetTotalAssignedLeads(),
                LEAD_TASKS.GetTotalLeads(),
                LEAD_TASKS.GetTodayLeads(),
                LEAD_TASKS.GetLeadTiles(),
                LEAD_TASKS.GetPlatformLeads()
            )

            # Unpack results from asyncio.gather
            unassignedLeads, assignedLeads, totalLeads, todayLeads, leadTiles, platformLeads = results

            # Combine all the fetched data into a single response
            response_data = {
                "unassignedLeads": unassignedLeads,
                "assignedLeads": assignedLeads,
                "platformLeads": platformLeads,
                "totalLeads": totalLeads,
                "todayLeads": todayLeads,
                "leadTiles": leadTiles,
            }

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message="All lead statistics fetched successfully.",
                code=RESPONSE_CODES.success,
                data=response_data
            )

        except Exception as e:
            await MY_METHODS.printStatus(f"[All Leads Stats Error]: {e}")
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Failed to fetch all lead statistics.",
                code=RESPONSE_CODES.error,
                data={"error": str(e)}
            )
    # New: Get Paginated Leads
    @classmethod
    async def GetPaginatedLeadsStats(cls, start_date=None, end_date=None, search_query=None, page_number=1, page_size=10):
        """
        Get paginated leads with optional filters for date, search query, and pagination.
        """
        try:
            # Delegate the task to LEAD_TASKS for paginated results
            leads_data = await LEAD_TASKS.GetLeadTiles(
                start_date=start_date,
                end_date=end_date,
                search_query=search_query,
                page_number=page_number,
                page_size=page_size
            )

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message="Paginated lead data fetched successfully.",
                code=RESPONSE_CODES.success,
                data=leads_data
            )

        except Exception as e:
            await MY_METHODS.printStatus(f"[Paginated Leads Stats Error]: {e}")
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Failed to fetch paginated lead data.",
                code=RESPONSE_CODES.error,
                data={"error": str(e)}
            )
    @classmethod
    async def GetAllUserBusinessStats(cls):
        """
        Get total clients, total businesses, and total users.
        """
        try:
            results = await asyncio.gather(
                ANALYTICS_TASKS.GetTotalClients(),
                ANALYTICS_TASKS.GetTotalBusiness(),
                ANALYTICS_TASKS.GetTotalUsers(),
            )

            total_clients, total_businesses, total_users = results

            response_data = {
                "clients": total_clients,
                "businesses": total_businesses,
                "users": total_users
            }

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message="Total clients, businesses, and users fetched successfully.",
                code=RESPONSE_CODES.success,
                data=response_data
            )

        except Exception as e:
            await MY_METHODS.printStatus(f"[GetAllUserBusinessStats Error]: {e}")
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Failed to fetch user/business stats.",
                code=RESPONSE_CODES.error,
                data={"error": str(e)}
            )

    # 2. Get Today Signups
    @classmethod
    async def GetTodaySignupsStats(cls):
        """
        Get today's signups for clients, businesses, and users.
        """
        try:
            today_signups = await ANALYTICS_TASKS.GetTodaySignups()

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message="Today's signups fetched successfully.",
                code=RESPONSE_CODES.success,
                data=today_signups
            )

        except Exception as e:
            await MY_METHODS.printStatus(f"[GetTodaySignupsStats Error]: {e}")
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Failed to fetch today's signups.",
                code=RESPONSE_CODES.error,
                data={"error": str(e)}
            )

    # 3. Get Charts (Clients, Businesses, Users)
    @classmethod
    async def GetChartsStats(cls):
        try:
            model_map = {
                "clients": CustomUser.objects.filter(type="client"),
                "businesses": Business.objects.all(),
                "users": CustomUser.objects.all(),
            }

            chart_data = await ANALYTICS_TASKS.GetGroupedChartData(model_map)
            await MY_METHODS.printStatus(f"[Chart Data]: {chart_data}")

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message="Charts fetched successfully.",
                code=RESPONSE_CODES.success,
                data=chart_data
            )

        except Exception as e:
            # Optionally log the error
            await MY_METHODS.printStatus(f"[GetChartsStats Error]: {e}")
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Failed to fetch charts.",
                code=RESPONSE_CODES.error,
                data={"error": str(e)}
            )
    @classmethod
    async def GetTotalNoOfUsers(cls):
        try:
            result = await ADMIN_PANEL_TASKS.GetTotalUsers()
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message="Total users fetched successfully.",
                code=RESPONSE_CODES.success,
                data={"totalUsers": result}
            )
        except Exception as e:
            await MY_METHODS.printStatus(f"[GetTotalNoOfUsers Error]: {e}")
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Failed to fetch total users.",
                code=RESPONSE_CODES.error,
                data={"error": str(e)}
            )

    @classmethod
    async def GetDailyUserData(cls):
        try:
            result = await ANALYTICS_TASKS.GetDailyUsersTask()
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message="Daily user data fetched successfully.",
                code=RESPONSE_CODES.success,
                data=result
            )
        except Exception as e:
            await MY_METHODS.printStatus(f"[GetDailyUserData Error]: {e}")
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Failed to fetch daily user data.",
                code=RESPONSE_CODES.error,
                data={"error": str(e)}
            )

    # controller for total users , business, total query and today signups
    @classmethod
    async def GetDashboardData(cls):
        try:
            total_users, total_businesses, total_queries, today_signups = await asyncio.gather(
                ADMIN_PANEL_TASKS.GetTotalUsers(),
                ADMIN_PANEL_TASKS.GetTotalBusinesses(),
                LEAD_TASKS.GetTotalLeads(),
                ANALYTICS_TASKS.GetTodayUserSignups()
            )

            response_data = {
                "totalUsers": total_users,
                "totalBusinesses": total_businesses,
                "totalQueries": total_queries,
                "todaySignups": today_signups
            }

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message="Dashboard data fetched successfully.",
                code=RESPONSE_CODES.success,
                data=response_data
            )

        except Exception as e:
            await MY_METHODS.printStatus(f"[GetDashboardData Error]: {e}")
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Failed to fetch dashboard data.",
                code=RESPONSE_CODES.error,
                data={"error": str(e)}
            )