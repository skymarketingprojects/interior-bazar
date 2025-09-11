from django.urls import path, include

from . import views

urlpatterns = [
    path('paginate-business/', views.GetBusinessTilesStatsView, name='get_business_tiles_stats'),
    path('dashboard/', views.GetAdminDashboardStatsView, name='get_admin_dashboard_stats'),
    path('leads/', views.GetPlatformLeadsStatsView, name='get_platform_leads_stats'),
    path('leads/stats/', views.GetAssignedLeadsTilesView, name='get_assigned_leads_stats'),
    path('signup/stats/',views.GetTodaySignupsStatsView, name='get_today_signups_stats'),
    path('chart/', views.GetChartsStatsView, name='get_chart_view'),
]