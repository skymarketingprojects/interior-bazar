from django.urls import path, include

from .views import AdminPanelViewsV1, AdminPanelViewsV2
from .Views.AdminLeadsViews import AdminLeadsViewsV1,AdminLeadsViewsV2
from .Views.AdminUserViews import AdminUserViews, SendUserCredentialsView

from .Views import AdminLeadsViews, BusinessInfoViews, PannelSearchViews, MatchLeadsViews, FinanceViews, GMBLeadsViews
from .Views import AuditViews, PaymentsViews
urlpatterns = [
    ############################################################
    # v3 Admin Ops Console — audit trail (promptsadmin task 45)
    ############################################################
    path('audit/', AuditViews.GetAuditLogView, name='admin_audit_log'),
    # Refund action (promptsadmin task 46) — level-3
    path('payments/<int:txnId>/refund/', PaymentsViews.RefundView, name='admin_payment_refund'),

    path('paginate-business/', AdminPanelViewsV1.GetBusinessTilesStatsView, name='get_business_tiles_stats'),
    path('dashboard/', AdminPanelViewsV1.GetAdminDashboardStatsView, name='get_admin_dashboard_stats'),
    path('leads/', AdminPanelViewsV1.GetPlatformLeadsStatsView, name='get_platform_leads_stats'),
    path('leads/stats/', AdminPanelViewsV1.GetAssignedLeadsTilesView, name='get_assigned_leads_stats'),
    path('signup/stats/',AdminPanelViewsV1.GetTodaySignupsStatsView, name='get_today_signups_stats'),
    path('chart/', AdminPanelViewsV1.GetChartsStatsView, name='get_chart_view'),
    path('total-users/', AdminPanelViewsV1.GetTotalUsersView, name='get_chart_view'),
    path('analytics/users/', AdminPanelViewsV1.GetDailyUsersStatsView, name='get_daily_users_view'),
    path('analytics/', AdminPanelViewsV1.GetDashboardDataView, name='get_daily_users_view'),

    ############################################################
    # Admin Panel Version 2
    ############################################################
    path('v2/paginate-business/', AdminPanelViewsV2.GetBusinessTilesStatsView, name='get_business_tiles_stats_v2'),
    path('v2/dashboard/', AdminPanelViewsV2.GetAdminDashboardStatsView, name='get_admin_dashboard_stats_v2'),
    path('v2/leads/', AdminPanelViewsV2.GetPlatformLeadsStatsView, name='get_platform_leads_stats_v2'),
    path('v2/leads/stats/', AdminPanelViewsV2.GetAssignedLeadsTilesView, name='get_assigned_leads_stats_v2'),
    path('v2/signup/stats/',AdminPanelViewsV2.GetTodaySignupsStatsView, name='get_today_signups_stats_v2'),
    path('v2/chart/', AdminPanelViewsV2.GetChartsStatsView, name='get_chart_view_v2'),
    path('v2/total-users/', AdminPanelViewsV2.GetTotalUsersView, name='get_chart_view_v2'),
    path('v2/analytics/users/', AdminPanelViewsV2.GetDailyUsersStatsView, name='get_daily_users_view_v2'),
    path('v2/analytics/leads/', AdminPanelViewsV2.GetLeadAnalyticsView, name='get_lead_analytics_v2'),
    path('v2/analytics/', AdminPanelViewsV2.GetDashboardDataView, name='get_daily_users_view_v2'),


    ############################################################
    # Pannel Search
    ############################################################
    path('business/search/<str:query>/', PannelSearchViews.SearchQueryView, name='admin_search'),
    path('business/<int:Id>/', PannelSearchViews.GetBusinessByIdView, name='business_data'),

    ############################################################
    # Business info
    ############################################################
    path('businesses/<int:pageNo>/<int:pageSize>/', BusinessInfoViews.GetAdminBusinessDataView, name='business_data_pagination'),
    path('v2/businesses/', BusinessInfoViews.GetAdminBusinessDataViewV2, name='business_data_pagination_v2'),
    path('v2/businesses/<int:businessId>/', BusinessInfoViews.DeleteBusinessDataView, name='business_delete'),
    path('v2/business/plan/',AdminPanelViewsV2.UpdatePlanIntentView, name='update_plan_intent'),
    
    ############################################################
    # leads
    ############################################################
    path('query/<int:pageNo>/<int:pageSize>/', AdminLeadsViewsV1.GetAdminQueryView, name='query_data'),
    path('v2/query/', AdminLeadsViewsV2.QueryViews.as_view(), name='query_data'),
    path('v2/query/<int:leadId>/', AdminLeadsViewsV2.QueryViews.as_view(), name='query_data_update'),
    path('lead/assign/', AdminLeadsViewsV1.AssignQueryView, name='assign_lead'),

    ############################################################
    # Match leads
    ############################################################
    path('leads/match/', MatchLeadsViews.MatchLeadsView, name='match_leads'),

    #########################################################
    # Funnel Query
    #########################################################
    path('funnel/<int:pageNumber>/<int:pageSize>/', AdminPanelViewsV2.GetFunnelQueriesView, name='GetFunnelQueriesView'),

    #Finance
    path('finance/', FinanceViews.getFinanceDataView, name='finance_view'),

    path('users/', AdminUserViews.as_view(), name='users_view'),
    path('users/<int:userId>', AdminUserViews.as_view(), name='users_view_with_id'),
    path('users/<int:userId>/send-credentials/', SendUserCredentialsView.as_view(), name='send_user_credentials'),

    ############################################################
    # GMB Leads (Flow from GEMINI.md & RANKING.md)
    ############################################################
    path('v1/ingest/gmb-data/', GMBLeadsViews.IngestGMBDataView, name='ingest_gmb_data'),
    path('v1/admin/all-leads/', GMBLeadsViews.GetAllLeadsView, name='get_all_gmb_leads'),
    path('v1/leads/my-leads/', GMBLeadsViews.GetMyLeadsView, name='get_my_gmb_leads'),
    path('v1/leads/assign/', GMBLeadsViews.AssignLeadView, name='assign_gmb_lead'),
    path('v1/leads/<int:leadId>/', GMBLeadsViews.UpdateGMBLeadView, name='update_gmb_lead'),
    path('v1/leads/create/', GMBLeadsViews.CreateSingleLeadView, name='create_gmb_lead'),
    # Superadmin Management & Distribution
    path('v1/leads/kpis/', GMBLeadsViews.GetGMBLeadsKPIsView, name='get_gmb_leads_kpis'),
    path('v1/admins/', GMBLeadsViews.ListGMBAdminsView, name='list_gmb_admins'),
    path('v1/leads/user/<int:userId>/', GMBLeadsViews.GetUserLeadsView, name='get_user_gmb_leads'),
    path('v1/leads/auto-assign/', GMBLeadsViews.AutoAssignLeadsView, name='auto_assign_gmb_leads'),
]