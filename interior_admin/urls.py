from django.urls import path, include

from . import views
from .Views import AdminLeadsViews, BusinessInfoViews,PannelSearchViews
urlpatterns = [
    path('paginate-business/', views.GetBusinessTilesStatsView, name='get_business_tiles_stats'),
    path('dashboard/', views.GetAdminDashboardStatsView, name='get_admin_dashboard_stats'),
    path('leads/', views.GetPlatformLeadsStatsView, name='get_platform_leads_stats'),
    path('leads/stats/', views.GetAssignedLeadsTilesView, name='get_assigned_leads_stats'),
    path('signup/stats/',views.GetTodaySignupsStatsView, name='get_today_signups_stats'),
    path('chart/', views.GetChartsStatsView, name='get_chart_view'),

    ############################################################
    # Pannel Search
    ############################################################

    path('business/search/<str:query>/', PannelSearchViews.SearchQueryView, name='admin_search'),
    path('business/<int:Id>/', PannelSearchViews.GetBusinessByIdView, name='business_data'),

    ############################################################
    # Business info
    ############################################################

    path('businesses/<int:pageNo>/<int:pageSize>/', BusinessInfoViews.GetAdminBusinessDataView, name='business_data_pagination'),
    
    ############################################################
    # leads
    ############################################################
    path('query/<int:pageNo>/<int:pageSize>/', AdminLeadsViews.GetAdminQueryView, name='query_data'),
]