from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.MyMethods import MY_METHODS


from .Tasks.AdminPanelBusinessTasks import ADMIN_PANEL_TASKS
from .Tasks.AdminPanelLeadTasks import LEAD_TASKS
from .Tasks.AdminPannelAnalyticsTask import ANALYTICS_TASKS
from .Tasks.AdminPanelBusinessTasks import ADMIN_PANEL_BUSINESS_TASKS_V2
from .Tasks.AdminPanelLeadTasks import ADMIN_PANEL_LEAD_TASKS_V2
from .Tasks.AdminPannelAnalyticsTask import ADMIN_ANALYTICS_TASKS_V2

from django.conf import settings
from app_ib.Utils.AppMode import APPMODE

import asyncio
from app_ib.models import CustomUser, Business, LeadQuery, PlanQuery, BusinessPlan, Subscription
from app_ib.decorators.ViewDecorator import controllerExceptionHandler

class ADMIN_PANEL_CONTROLLER:

    # Existing Business Methods
    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.business_tile_fetch_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.business_tile_fetch_success
    )
    async def GetBusinessTilesStats(cls, start_date=None, end_date=None, page_number=1, page_size=2):
        tiles_data = await ADMIN_PANEL_TASKS.GetBusinessTiles(
            start_date=start_date,
            end_date=end_date,
            page_number=page_number,
            page_size=page_size
        )

        return tiles_data

    # Dashboard Stats
    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.dashboard_fetch_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.dashboard_fetch_success
    )
    async def GetAdminDashboardStats(cls):
        """
        Returns full dashboard stats with totals and all tile data (no filters).
        """
        results = await asyncio.gather(
            ADMIN_PANEL_TASKS.GetTotalBusinesses(),
            ADMIN_PANEL_TASKS.GetTotalActiveBusinesses(),
            ADMIN_PANEL_TASKS.GetTotalInactiveBusinesses(),
            ADMIN_PANEL_TASKS.GetWeeklySignups(),
            ADMIN_PANEL_TASKS.GetBusinessTiles(),
        )

        # Each result is a (status, data) tuple
        (total_businesses_status, total_businesses) = results[0]
        (total_active_status, total_active) = results[1]
        (total_inactive_status, total_inactive) = results[2]
        (weekly_signups_status, weekly_signups) = results[3]
        (all_tiles_status, all_tiles) = results[4]


        dashboard_data = {
            "totalBusinesses": total_businesses,
            "totalActiveBusinesses": total_active,
            "totalInactiveBusinesses": total_inactive,
            "weeklySignups": weekly_signups,
            "businessTiles": all_tiles
        }

        return True,dashboard_data

    # New: Get All Leads (without pagination)
    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.lead_tile_fetch_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.lead_tile_fetch_success
    )
    async def GetAllLeadsStats(cls, start_date=None, end_date=None, search_query=None):
        """
        Get all lead statistics (total platform leads, assigned leads, total leads, today's leads, and lead tiles).
        """
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
        (unassignedLeadsstatus,unassignedLeads), (assignStatus,assignedLeads), (totalstatus,totalLeads), (todayStatus,todayLeads), (leadstatus,leadTiles), (platformStatus,platformLeads) = results

            # Combine all the fetched data into a single response
        response_data = {
            "unassignedLeads": unassignedLeads,
            "assignedLeads": assignedLeads,
            "platformLeads": platformLeads,
            "totalLeads": totalLeads,
            "todayLeads": todayLeads,
            "leadTiles": leadTiles,
        }

        return True,response_data
    # New: Get Paginated Leads
    
    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.paginated_leads_fetch_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.paginated_leads_fetch_success
    )
    async def GetPaginatedLeadsStats(cls, start_date=None, end_date=None, search_query=None, page_number=1, page_size=10):
        """
        Get paginated leads with optional filters for date, search query, and pagination.
        """
        # Delegate the task to LEAD_TASKS for paginated results
        leads_data = await LEAD_TASKS.GetLeadTiles(
            start_date=start_date,
            end_date=end_date,
            search_query=search_query,
            page_number=page_number,
            page_size=page_size
        )

        return leads_data
        

    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.user_business_fetch_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.user_business_fetch_success
    )
    async def GetAllUserBusinessStats(cls):
        """
        Get total clients, total businesses, and total users.
        """
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

        return response_data

    # 2. Get Today Signups
    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.today_signups_fetch_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.today_signups_fetch_success
    )
    async def GetTodaySignupsStats(cls):
        """
        Get today's signups for clients, businesses, and users.
        """
        today_signups = await ANALYTICS_TASKS.GetTodaySignups()

        return today_signups


    # 3. Get Charts (Clients, Businesses, Users)
    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.charts_fetch_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.charts_fetch_success
    )
    async def GetChartsStats(cls):
        model_map = {
            "clients": CustomUser.objects.filter(type="client"),
            "businesses": Business.objects.all(),
            "users": CustomUser.objects.all(),
        }

        chart_data = await ANALYTICS_TASKS.GetGroupedChartData(model_map)

        return chart_data

    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.total_users_fetch_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.total_users_fetch_success
    )
    async def GetTotalNoOfUsers(cls):
        result = await ADMIN_PANEL_TASKS.GetTotalUsers()
        return result

    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.daily_user_fetch_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.daily_user_fetch_success
    )
    async def GetDailyUserData(cls):
        result = await ANALYTICS_TASKS.GetDailyUsersTask()
        return result

    # controller for total users , business, total query and today signups
    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.dashboard_data_fetch_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.dashboard_data_fetch_success
    )
    async def GetDashboardData(cls):
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

        return response_data
    


class ADMIN_PANEL_CONTROLLER_V2:

    # ---------------- BUSINESS TILES ----------------
    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.business_tile_fetch_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.business_tile_fetch_success
    )
    async def GetBusinessTilesStats(cls, start_date=None, end_date=None, page_number=1, page_size=2,plan=None):

        business_qs = None
        if plan:
            business_qs = Business.objects.filter(
                business_plan__plan_id=plan
            )
        else:
            business_qs = Business.objects.all()


        if settings.ENV == APPMODE.PROD:
            business_qs = business_qs.filter(selfCreated=False)

        tiles_data = await ADMIN_PANEL_BUSINESS_TASKS_V2.GetBusinessTiles(
            business_qs=business_qs,
            start_date=start_date,
            end_date=end_date,
            page_number=page_number,
            page_size=page_size
        )

        return tiles_data


    # ---------------- DASHBOARD BUSINESS STATS ----------------
    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.dashboard_fetch_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.dashboard_fetch_success
    )
    async def GetAdminDashboardStats(cls):
        business_qs = Business.objects.all()
        if settings.ENV == APPMODE.PROD:
            business_qs = business_qs.filter(selfCreated=False)  # Correct usage in classmethod

        # Kick off both async tasks
        metrics_task = ADMIN_PANEL_BUSINESS_TASKS_V2.GetBusinessMetrics(business_qs)
        tiles_task = ADMIN_PANEL_BUSINESS_TASKS_V2.GetBusinessTiles(business_qs=business_qs)

        # Each task returns (status, data)
        (metrics_status, metrics_data), (tiles_status, tiles_data) = await asyncio.gather(
            metrics_task, tiles_task
        )

        # Build dashboard using the returned data
        dashboard_data = {
            "totalBusinesses": metrics_data.get("total", 0),
            "totalActiveBusinesses": metrics_data.get("active", 0),
            "totalInactiveBusinesses": metrics_data.get("inactive", 0),
            "weeklySignups": metrics_data.get("weekly_signup", 0),
            "businessTiles": tiles_data  # Already contains results + pagination
        }

        return True,dashboard_data



    # ---------------- ALL LEAD STATS ----------------
    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.lead_tile_fetch_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.lead_tile_fetch_success
    )
    async def GetAllLeadsStats(cls, start_date=None, end_date=None, search_query=None):

        lead_qs = LeadQuery.objects.all()
        plan_qs = PlanQuery.objects.all()

        metrics_task = ADMIN_PANEL_LEAD_TASKS_V2.GetLeadMetrics(
            lead_qs=lead_qs,
            plan_qs=plan_qs
        )

        tiles_task = ADMIN_PANEL_LEAD_TASKS_V2.GetLeadTiles(
            lead_qs=lead_qs,
            start_date=start_date,
            end_date=end_date,
            search_query=search_query
        )

        (metricstatus,metrics),(GetAllLeadsStats,tiles) = await asyncio.gather(metrics_task, tiles_task)

        response_data = {
            "unassignedLeads": metrics["unassigned"],
            "assignedLeads": metrics["assigned"],
            "platformLeads": metrics["platform"],
            "totalLeads": metrics["final_total"],
            "todayLeads": metrics["today"],
            "leadTiles": tiles,
        }

        return True,response_data


    # ---------------- PAGINATED LEADS ----------------
    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.paginated_leads_fetch_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.paginated_leads_fetch_success
    )
    async def GetPaginatedLeadsStats(cls, start_date=None, end_date=None, search_query=None, page_number=1, page_size=10):

        lead_qs = LeadQuery.objects.all()

        leads_data = await ADMIN_PANEL_LEAD_TASKS_V2.GetLeadTiles(
            lead_qs=lead_qs,
            start_date=start_date,
            end_date=end_date,
            search_query=search_query,
            page_number=page_number,
            page_size=page_size
        )

        return leads_data


    # ---------------- USER / BUSINESS TOTALS ----------------
    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.user_business_fetch_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.user_business_fetch_success
    )
    async def GetAllUserBusinessStats(cls):

        user_qs = CustomUser.objects.all()
        client_qs = CustomUser.objects.filter(type="client")
        business_qs = Business.objects.all()

        if settings.ENV == APPMODE.PROD:
            user_qs = user_qs.filter(selfCreated=False)
            client_qs = client_qs.filter(selfCreated=False)
            business_qs = business_qs.filter(selfCreated=False)

        totals = await ADMIN_ANALYTICS_TASKS_V2.GetSystemTotals(
            user_qs=user_qs,
            client_qs=client_qs,
            business_qs=business_qs
        )

        return totals


    # ---------------- TODAY SIGNUPS ----------------
    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.today_signups_fetch_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.today_signups_fetch_success
    )
    async def GetTodaySignupsStats(cls):

        user_qs = CustomUser.objects.all()
        client_qs = CustomUser.objects.filter(type="client")
        business_qs = Business.objects.all()

        if settings.ENV == APPMODE.PROD:
            user_qs = user_qs.filter(selfCreated=False)
            client_qs = client_qs.filter(selfCreated=False)
            business_qs = business_qs.filter(selfCreated=False)

        today_data = await ADMIN_ANALYTICS_TASKS_V2.GetTodayTotals(
            user_qs=user_qs,
            client_qs=client_qs,
            business_qs=business_qs
        )

        return today_data


    # ---------------- CHARTS ----------------
    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.charts_fetch_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.charts_fetch_success
    )
    async def GetChartsStats(cls):

        model_map = {
            "clients": CustomUser.objects.filter(type="client"),
            "businesses": Business.objects.all(),
            "users": CustomUser.objects.all(),
        }

        if settings.ENV == APPMODE.PROD:
            model_map["clients"] = model_map["clients"].filter(selfCreated=False)
            model_map["businesses"] = model_map["businesses"].filter(selfCreated=False)
            model_map["users"] = model_map["users"].filter(selfCreated=False)

        chart_data = await ADMIN_ANALYTICS_TASKS_V2.GetGroupedChartData(model_map)

        return chart_data


    # ---------------- TOTAL USERS ----------------
    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.total_users_fetch_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.total_users_fetch_success
    )
    async def GetTotalNoOfUsers(cls):

        user_qs = CustomUser.objects.all()
        if settings.ENV == APPMODE.PROD:
            user_qs = user_qs.filter(selfCreated=False)

        result = await ADMIN_PANEL_BUSINESS_TASKS_V2.GetUserMetrics(user_qs)

        return result


    # ---------------- DAILY USERS ----------------
    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.daily_user_fetch_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.daily_user_fetch_success
    )
    async def GetDailyUserData(cls):

        user_qs = CustomUser.objects.all()
        if settings.ENV == APPMODE.PROD:
            user_qs = user_qs.filter(selfCreated=False)

        model_map = {"users": user_qs}
        result = await ADMIN_ANALYTICS_TASKS_V2.GetGroupedChartData(model_map)

        return result


    # ---------------- DASHBOARD CORE ----------------
    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.dashboard_data_fetch_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.dashboard_data_fetch_success
    )
    async def GetDashboardData(cls):

        user_qs = CustomUser.objects.all()
        business_qs = Business.objects.all()
        lead_qs = LeadQuery.objects.all()
        plan_qs = PlanQuery.objects.all()

        if settings.ENV == APPMODE.PROD:
            user_qs = user_qs.filter(selfCreated=False)
            business_qs = business_qs.filter(selfCreated=False)

        users_task = ADMIN_PANEL_BUSINESS_TASKS_V2.GetUserMetrics(user_qs)
        business_task = ADMIN_PANEL_BUSINESS_TASKS_V2.GetBusinessMetrics(business_qs)
        lead_task = ADMIN_PANEL_LEAD_TASKS_V2.GetLeadMetrics(lead_qs, plan_qs)
        today_task = ADMIN_ANALYTICS_TASKS_V2.GetTodayTotals(
            user_qs=user_qs,
            client_qs=user_qs.filter(type="client"),
            business_qs=business_qs
        )

        users, business, leads, today = await asyncio.gather(
            users_task,
            business_task,
            lead_task,
            today_task
        )

        return True,{
            "totalUsers": users["total"],
            "totalBusinesses": business["total"],
            "totalQueries": leads["final_total"],
            "todaySignups": today["users"]
        }
