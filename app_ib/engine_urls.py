"""URL routes for the v2.1.0.0/v2.1.1 discovery engine, mounted under /api/v1/engine/."""
from django.urls import path
from app_ib.Views import (EngineView, EngineCrudView, EngineSSEView, EngineChatView,
                          EngineHomeView, EngineExploreView, EngineGapsView)
from app_ib.Views import EngineHomeBannerView  # hero carousel slides (own file — parallel-work safe)
from app_ib.Views import EngineStockView  # stock/availability (own file — parallel-work safe)

urlpatterns = [
    # --- Explore page sections ---
    path("explore/search-cards/", EngineExploreView.ExploreSearchCardsView, name="EngineExploreSearchCardsView"),
    path("explore/editors-pick/", EngineExploreView.EditorsPickView, name="EngineEditorsPickView"),       # 1
    path("explore/design-ideas/", EngineExploreView.DesignIdeasView, name="EngineDesignIdeasView"),        # 2
    path("architect/<int:architectId>/projects/", EngineExploreView.ProjectCreateView, name="EngineProjectCreateView"),
    # --- Home page sections ---
    path("home/filters/", EngineHomeView.HomeFiltersView, name="EngineHomeFiltersView"),         # 0 filter bar pills
    path("home/banners/", EngineHomeBannerView.HomeBannersView, name="EngineHomeBannersView"),   # home hero carousel slides
    path("banners/", EngineHomeBannerView.BannersView, name="EngineBannersView"),                # per-page hero slides (?page=)
    path("home/cities/", EngineHomeView.HomeCitiesView, name="EngineHomeCitiesView"),             # 0b browse by location
    path("home/reels/", EngineHomeView.ReelsView, name="EngineReelsView"),                       # 1 trending reels
    path("home/for-you/<str:entityType>/", EngineHomeView.ForYouView, name="EngineForYouView"),  # 2,3,4,7 recommendations
    path("home/architects/", EngineHomeView.ArchitectsRecommendedView, name="EngineArchitectsRecommendedView"),  # 5 (legacy) architects
    path("home/verified-businesses/", EngineHomeView.VerifiedBusinessesView, name="EngineVerifiedBusinessesView"),  # 5b verified-business score
    path("home/fresh-catalogues/", EngineHomeView.FreshCataloguesView, name="EngineFreshCataloguesView"),  # 7b Fresh from manufacturers
    path("home/get-inspired/", EngineHomeView.GetInspiredView, name="EngineGetInspiredView"),  # 8 Get inspired gallery
    path("home/differentiators/", EngineHomeView.DifferentiatorsView, name="EngineDifferentiatorsView"),  # What makes IB different
    path("home/join-us/", EngineHomeView.JoinUsView, name="EngineJoinUsView"),  # Join us final CTA band
    path("home/shops-nearby/", EngineHomeView.ShopsNearbyView, name="EngineShopsNearbyView"),     # 6 shops near you
    path("home/testimonials/", EngineHomeView.TestimonialsView, name="EngineTestimonialsView"),   # 9 video stories
    path("home/random-reviews/", EngineHomeView.RandomReviewsView, name="EngineRandomReviewsView"),  # 11 in their words
    # --- THE single per-user SSE connection (notifications + chat + feed) ---
    # item 12: ?token= auth supported — replaced with EngineGapsView.UserStreamTokenView
    path("stream/", EngineGapsView.UserStreamTokenView, name="EngineUserStreamView"),
    # --- Chat (send via REST, receive via /stream/) ---
    path("chat/conversations/", EngineChatView.ConversationListCreateView, name="EngineConversationListCreateView"),
    path("chat/conversations/<int:convId>/accept/", EngineChatView.ConversationAcceptView, name="EngineConversationAcceptView"),
    path("chat/conversations/<int:convId>/decline/", EngineChatView.ConversationDeclineView, name="EngineConversationDeclineView"),
    path("chat/conversations/<int:convId>/close/", EngineChatView.ConversationCloseView, name="EngineConversationCloseView"),
    path("chat/conversations/<int:convId>/mark-unread/", EngineChatView.ConversationMarkUnreadView, name="EngineConversationMarkUnreadView"),
    path("chat/conversations/<int:convId>/report/", EngineChatView.ConversationReportView, name="EngineConversationReportView"),
    path("chat/conversations/<int:convId>/delete/", EngineChatView.ConversationDeleteView, name="EngineConversationDeleteView"),
    path("chat/conversations/<int:convId>/labels/", EngineChatView.ConversationLabelsView, name="EngineConversationLabelsView"),
    path("chat/conversations/<int:convId>/events/", EngineChatView.ConversationEventsView, name="EngineConversationEventsView"),
    path("chat/conversations/<int:convId>/messages/", EngineChatView.MessagesView, name="EngineMessagesView"),
    path("chat/conversations/<int:convId>/read/", EngineChatView.MessagesReadView, name="EngineMessagesReadView"),
    # polling replacement for the SSE chat event (SSE /stream/ kept for future scale)
    path("chat/poll/", EngineChatView.ChatPollView, name="EngineChatPollView"),
    # --- Shop CRUD (write methods) + public GET by id (item 8) ---
    path("shop/create/", EngineCrudView.ShopCreateView, name="EngineShopCreateView"),
    path("shop/<int:shopId>/publish/", EngineCrudView.ShopPublishView, name="EngineShopPublishView"),  # F4 — must precede shop/<id>/
    path("shop/slug/<slug:slug>/", EngineGapsView.ShopBySlugView, name="EngineShopBySlugView"),
    path("shop/<int:shopId>/", EngineGapsView.ShopDetailView, name="EngineShopDetailView"),
    # --- Authenticated owner lists (mine/) — must come before shops/ to avoid prefix clash ---
    path("shops/mine/", EngineGapsView.MyShopsView, name="EngineMyShopsView"),
    # --- Public shop list (item 8) — must come after shop/slug/, shop/create/, and shops/mine/ ---
    path("shops/categories/", EngineGapsView.ShopCategoriesView, name="EngineShopCategoriesView"),  # filter bar taxonomy
    path("shops/", EngineGapsView.ShopsListView, name="EngineShopsListView"),
    # --- Architect CRUD (write methods) + public GET by id (item 8) ---
    path("architect/create/", EngineCrudView.ArchitectCreateView, name="EngineArchitectCreateView"),
    path("business/create/", EngineCrudView.BusinessCreateView, name="EngineBusinessCreateView"),  # buy-first business create (Prompt 7)
    path("architect/slug/<slug:slug>/", EngineGapsView.ArchitectBySlugView, name="EngineArchitectBySlugView"),
    path("architect/<int:architectId>/", EngineGapsView.ArchitectDetailView, name="EngineArchitectDetailView"),
    # --- Authenticated owner list (mine/) — must come before architects/ to avoid prefix clash ---
    path("architects/mine/", EngineGapsView.MyArchitectsView, name="EngineMyArchitectsView"),
    # --- Public architect list (item 8) ---
    path("architects/categories/", EngineGapsView.ArchitectCategoriesView, name="EngineArchitectCategoriesView"),  # filter bar taxonomy
    path("architects/", EngineGapsView.ArchitectsListView, name="EngineArchitectsListView"),
    # --- Business public detail (core + related offerings + review summary) ---
    path("business/slug/<slug:slug>/", EngineGapsView.BusinessBySlugView, name="EngineBusinessBySlugView"),
    # Per-business offering lists (paginated) — must precede the bare detail route so the
    # /products|/services|/catalogues suffixes are matched before business/<id>/.
    path("business/<int:businessId>/products/", EngineGapsView.BusinessProductsView, name="EngineBusinessProductsView"),
    path("business/<int:businessId>/services/", EngineGapsView.BusinessServicesView, name="EngineBusinessServicesView"),
    path("business/<int:businessId>/catalogues/", EngineGapsView.BusinessCataloguesView, name="EngineBusinessCataloguesView"),
    path("business/<int:businessId>/publish/", EngineCrudView.BusinessPublishView, name="EngineBusinessPublishView"),  # F2
    path("business/<int:businessId>/", EngineGapsView.BusinessDetailView, name="EngineBusinessDetailView"),
    # --- Entity-typed subscription plans (buy-first model, Prompt 6) ---
    path("my/plans/", EngineGapsView.MyPlansView, name="EngineMyPlansView"),          # auth: buying history union
    path("my/invoices/", EngineGapsView.MyInvoicesView, name="EngineMyInvoicesView"),  # auth: invoice/billing history
    path("my/activity/", EngineGapsView.MyActivityView, name="EngineMyActivityView"),  # auth: view+click event feed (own browsing)
    path("my/engagement/", EngineGapsView.MyEngagementView, name="EngineMyEngagementView"),  # auth: inbound activity on owned entities
    path("my/engagement/read/", EngineGapsView.MyEngagementReadView, name="EngineMyEngagementReadView"),  # auth: mark feed read
    path("support-config/", EngineGapsView.SupportConfigView, name="EngineSupportConfigView"),  # public: support/contact channels (task 75)
    path("brand-logo/", EngineGapsView.BrandLogoPublicView, name="EngineBrandLogoView"),  # public: today's active brand logo (task 27)
    path("team/", EngineGapsView.TeamMembersView, name="EngineTeamMembersView"),  # public: About team grid (task 77)
    path("help/content/", EngineGapsView.HelpContentView, name="EngineHelpContentView"),  # public: FAQs/topics/tutorials (task 76)
    path("support/tickets/", EngineGapsView.SupportTicketsView, name="EngineSupportTicketsView"),  # POST raise / GET my tickets (task 76)
    path("my/quotations/", EngineGapsView.MyQuotationsView, name="EngineMyQuotationsView"),  # auth: seller's own quotations
    path("quotations/", EngineGapsView.QuotationCreateView, name="EngineQuotationCreateView"),  # auth: create quotation (task 63)
    path("quotations/<int:quotationId>/", EngineGapsView.QuotationUpdateView, name="EngineQuotationUpdateView"),  # auth: update owned quotation
    path("quotations/<int:quotationId>/status/", EngineGapsView.QuotationStatusView, name="EngineQuotationStatusView"),  # auth: transition status
    path("quotations/<int:quotationId>/send/", EngineGapsView.QuotationSendView, name="EngineQuotationSendView"),  # auth: send to buyer (F12)
    # Phase 2 — active-sessions dashboard (JWT session management)
    path("my/sessions/", EngineGapsView.MySessionsView, name="EngineMySessionsView"),  # auth: list active sessions
    path("my/sessions/<int:sessionId>/revoke/", EngineGapsView.RevokeSessionView, name="EngineRevokeSessionView"),  # auth: revoke one session
    path("my/sessions/revoke-all/", EngineGapsView.RevokeAllSessionsView, name="EngineRevokeAllSessionsView"),  # auth: sign out everywhere (task 81)
    path("plans/templates/", EngineGapsView.PlanTemplatesView, name="EnginePlanTemplatesView"),  # public catalogue (?entityType=)
    path("plans/upgrade/preview/", EngineGapsView.UpgradePreviewView, name="EngineUpgradePreviewView"),  # auth: upgrade settlement preview (Prompt 9)
    path("plans/change/", EngineGapsView.ChangePlanView, name="EngineChangePlanView"),  # in-dashboard upgrade/downgrade (task 61)
    path("plans/manual/", EngineGapsView.ManualPlanView, name="EngineManualPlanView"),  # auth: manual (offline) plan purchase → inactive plan + become seller
    path("payment/recheck/", EngineGapsView.PaymentRecheckView, name="EnginePaymentRecheckView"),  # auth: manual single-txn re-verify (Prompt 10)
    path("server-time/", EngineGapsView.ServerTimeView, name="EngineServerTimeView"),  # backend-authoritative clock (Prompt 12)
    # --- Public catalog lists (item 8 — businesses/products/services/catalogues) ---
    path("businesses/categories/", EngineGapsView.BusinessCategoriesView, name="EngineBusinessCategoriesView"),  # filter bar taxonomy
    path("businesses/", EngineGapsView.BusinessesListView, name="EngineBusinessesListView"),
    path("products/categories/", EngineGapsView.ProductCategoriesView, name="EngineProductCategoriesView"),  # filter sidebar taxonomy
    path("products/", EngineGapsView.ProductsListView, name="EngineProductsListView"),
    path("services/categories/", EngineGapsView.ServiceCategoriesView, name="EngineServiceCategoriesView"),  # filter bar taxonomy
    path("services/", EngineGapsView.ServicesListView, name="EngineServicesListView"),
    path("catalogues/", EngineGapsView.CataloguesListView, name="EngineCataloguesListView"),
    path("catalogues/<str:slugOrId>/", EngineGapsView.CatalogueDetailView, name="EngineCatalogueDetailView"),
    # --- Stock / availability (products have stock; services only available/not) ---
    path("product/<int:productId>/availability/", EngineStockView.ProductAvailabilityView, name="EngineProductAvailabilityView"),
    path("product/<int:productId>/stock/check/", EngineStockView.ProductStockCheckView, name="EngineProductStockCheckView"),
    path("service/<int:serviceId>/availability/", EngineStockView.ServiceAvailabilityView, name="EngineServiceAvailabilityView"),  # GET public, PATCH owner-only
    # --- Entity resolve (public, AllowAny) ---
    path("resolve/<str:entityType>/<slug:slug>/", EngineGapsView.ResolveEntityView, name="EngineResolveEntityView"),
    # --- Review CRUD ---
    path("reviews/", EngineCrudView.ReviewListCreateView, name="EngineReviewListCreateView"),
    path("reviews/<int:reviewId>/", EngineCrudView.ReviewUpdateDeleteView, name="EngineReviewUpdateDeleteView"),
    path("reviews/<int:reviewId>/helpful/", EngineCrudView.ReviewHelpfulView, name="EngineReviewHelpfulView"),
    path("reviews/<int:reviewId>/reply/", EngineCrudView.ReviewReplyView, name="EngineReviewReplyView"),  # seller reply + tags (task 64)
    # --- Video CRUD (item 9) ---
    path("videos/<str:entityType>/<int:objectId>/", EngineGapsView.VideoListCreateView, name="EngineVideoListCreateView"),
    path("videos/<int:videoId>/set-primary/", EngineGapsView.VideoSetPrimaryView, name="EngineVideoSetPrimaryView"),
    path("videos/<int:videoId>/", EngineGapsView.VideoUpdateDeleteView, name="EngineVideoUpdateDeleteView"),
    # --- SSE / live feed ---
    path("feed/live/", EngineSSEView.LiveFeedInitView, name="EngineLiveFeedInitView"),
    path("feed/live/stream/", EngineSSEView.LiveFeedSSEView, name="EngineLiveFeedSSEView"),
    # polling batch for the live ticker — 20 events per call (SSE stream kept for scale)
    path("feed/batch/", EngineSSEView.LiveFeedBatchView, name="EngineLiveFeedBatchView"),
    # back-compat alias -> the same unified per-user stream (with ?token= support)
    path("notifications/stream/", EngineGapsView.UserStreamTokenView, name="EngineNotificationSSEView"),
    # trending
    path("trending/businesses/", EngineView.TrendingBusinessesView, name="EngineTrendingBusinessesView"),
    path("trending/products/", EngineView.TrendingProductsView, name="EngineTrendingProductsView"),
    path("trending/services/", EngineGapsView.TrendingServicesView, name="EngineTrendingServicesView"),   # item 1
    path("trending/categories/", EngineGapsView.TrendingCategoriesView, name="EngineTrendingCategoriesView"),  # item 2
    path("trending/kpi/", EngineGapsView.TrendingKpiView, name="EngineTrendingKpiView"),                  # item 3
    path("trending/searches/", EngineView.TrendingSearchesView, name="EngineTrendingSearchesView"),
    path("trending/city/", EngineView.CityPulseView, name="EngineCityPulseView"),
    # leaderboard + momentum
    path("leaderboard/", EngineView.LeaderboardView, name="EngineLeaderboardView"),
    path("trending/momentum/", EngineView.MomentumView, name="EngineMomentumView"),
    # discovery
    path("discovery/most-saved/", EngineView.MostSavedView, name="EngineMostSavedView"),
    path("discovery/behind-the-trend/", EngineView.BehindTheTrendView, name="EngineBehindTheTrendView"),
    # completion
    path("completion/<str:entityType>/<int:objectId>/", EngineView.CompletionView, name="EngineCompletionView"),
    # events
    path("events/view/", EngineView.TrackViewView, name="EngineTrackViewView"),
    path("events/click/", EngineView.TrackClickView, name="EngineTrackClickView"),
    path("events/search/", EngineView.TrackSearchView, name="EngineTrackSearchView"),
    # user state
    path("saved/check/", EngineGapsView.SavedCheckView, name="EngineSavedCheckView"),              # item 4
    path("saved/", EngineView.SavedItemsView, name="EngineSavedItemsView"),
    path("recently-viewed/clear/", EngineGapsView.RecentlyViewedClearView, name="EngineRecentlyViewedClearView"),  # item 5
    path("recently-viewed/summary/", EngineGapsView.RecentlyViewedSummaryView, name="EngineRecentlyViewedSummaryView"),  # Phase 1
    path("recently-viewed/export/", EngineView.RecentlyViewedExportView, name="EngineRecentlyViewedExportView"),  # CSV download: Name + Viewed at only
    path("recently-viewed/<int:row_id>/", EngineGapsView.RecentlyViewedRemoveView, name="EngineRecentlyViewedRemoveView"),  # per-item delete (task 45)
    path("recently-viewed/", EngineView.RecentlyViewedView, name="EngineRecentlyViewedView"),
    path("feedback/", EngineGapsView.MyFeedbackListView, name="EngineMyFeedbackListView"),  # user's own reports/feedback (task 48)
    path("settings/", EngineGapsView.UserSettingsView, name="EngineUserSettingsView"),  # notification/privacy prefs (task 49)
    path("account/deactivate/", EngineGapsView.DeactivateAccountView, name="EngineDeactivateAccountView"),  # task 49
    path("notifications/", EngineView.NotificationsView, name="EngineNotificationsView"),
    path("notifications/unread-count/", EngineView.NotificationUnreadCountView, name="EngineNotificationUnreadCountView"),
    path("notifications/mark-all-read/", EngineGapsView.NotificationsMarkAllReadView, name="EngineNotificationsMarkAllReadView"),
    path("autogrowth/", EngineGapsView.AutogrowthView, name="EngineAutogrowthView"),  # seller keyword targeting (task 58)
    path("autogrowth/<int:keywordId>/", EngineGapsView.AutogrowthRemoveView, name="EngineAutogrowthRemoveView"),
    # dashboard + analytics (items 6, 7)
    path("dashboard/kpis/", EngineGapsView.DashboardKpisView, name="EngineDashboardKpisView"),
    path("analytics/chart/", EngineGapsView.AnalyticsChartView, name="EngineAnalyticsChartView"),
    # leads (item 10)
    path("leads/", EngineGapsView.LeadCreateView, name="EngineLeadCreateView"),  # buyer-facing connect wizard
    path("leads/manual/", EngineGapsView.LeadManualCreateView, name="EngineLeadManualCreateView"),  # seller-logged off-platform enquiry
    path("leads/prioritized/", EngineGapsView.LeadsPrioritizedView, name="EngineLeadsPrioritizedView"),
    path("leads/<int:leadId>/accept/", EngineGapsView.LeadAcceptView, name="EngineLeadAcceptView"),
    path("leads/<int:leadId>/stage/", EngineGapsView.LeadStageView, name="EngineLeadStageView"),  # kanban stage persist (task 62)
    path("leads/<int:leadId>/decline/", EngineGapsView.LeadDeclineView, name="EngineLeadDeclineView"),
    # platform ads (item 11)
    path("ads/", EngineGapsView.AdsListView, name="EngineAdsListView"),
    path("ads/<int:adId>/click/", EngineGapsView.AdClickView, name="EngineAdClickView"),
    # credentials CRUD — Award + ProcessStep + Expertise (Phase 1, item 16)
    path("credentials/award/", EngineGapsView.AwardCreateView, name="EngineAwardCreateView"),
    path("credentials/award/<int:awardId>/", EngineGapsView.AwardUpdateDeleteView, name="EngineAwardUpdateDeleteView"),
    path("credentials/process-step/", EngineGapsView.ProcessStepCreateView, name="EngineProcessStepCreateView"),
    path("credentials/process-step/<int:stepId>/", EngineGapsView.ProcessStepUpdateDeleteView, name="EngineProcessStepUpdateDeleteView"),
    path("credentials/expertise/", EngineGapsView.ExpertiseSetView, name="EngineExpertiseSetView"),
    # Phase 3 — RelatedItem / Newsletter / Blog featured / Catalogue trending / Engine profile
    path("related/<str:entityType>/<int:objectId>/", EngineGapsView.RelatedItemsView, name="EngineRelatedItemsView"),
    path("newsletter/subscribe/", EngineGapsView.NewsletterSubscribeView, name="EngineNewsletterSubscribeView"),
    path("blog/featured/", EngineGapsView.FeaturedBlogsView, name="EngineFeaturedBlogsView"),
    path("trending/catalogues/", EngineGapsView.TrendingCataloguesView, name="EngineTrendingCataloguesView"),
    path("my/profile/", EngineGapsView.MyProfileView, name="EngineMyProfileView"),
    path("my/change-password/", EngineGapsView.ChangePasswordView, name="EngineChangePasswordView"),  # auth: change own password
]
