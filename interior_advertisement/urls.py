from django.urls import path
from . import views
urlpatterns = [
    # ---------------- AD CAMPAIGN ----------------
    path("campaign/create/", views.CreateCampaignView, name="campaign-create"),
    path("campaign/<int:campaign_id>/update/", views.UpdateCampaignView, name="campaign-update"),
    path("campaign/<int:campaign_id>/", views.GetCampaignView, name="campaign-detail"),
    path("campaigns/", views.GetCampaignsByBusinessView, name="campaign-list"),
    path("campaign/placement/<int:placementId>/", views.GetActiveCampaignsView, name='campaign-list-by-placement'),

    # ---------------- AD ASSET ----------------
    path("campaign/<int:campaign_id>/asset/create/", views.AdAssetCreateView, name="asset-create"),
    path("campaign/<int:campaign_id>/asset/", views.GetAdAssetsByCampaignView, name="asset-list-by-campaign"),

    # ---------------- AD PAYMENT ----------------
    path("campaign/<int:campaign_id>/payment/create/", views.AdPaymentCreateView, name="payment-create"),

    # ---------------- AD EVENT ----------------
    path("campaign/<int:campaign_id>/event/create/", views.AdEventCreateView, name="event-create"),

    # ---------------- AD PERSONA ----------------
    path("campaign/<int:campaignId>/persona/create/", views.CreateAdPersonaView, name="persona-create"),
    path("campaign/<int:campaignId>/persona/", views.GetAdPersonaView, name="persona-list"),

    # ---------------- ENUM JSON ----------------
    path('enums/status/', views.getAdStatusEnum, name="status"),
    path('enums/approval-mode/', views.getAdApprovalModeEnum, name= "approval-mode"),
    path('enums/asset-type/', views.getAdAssetTypeEnum,name = "asset-type"),
    path('enums/payment-status/', views.getAdPaymentStatusEnum,name="payment-status"),
    path('enums/event-type/', views.getAdEventTypeEnum,name="event-type"),
    path('enums/placement/', views.getAdPlacementEnum,name="placement"),
]
