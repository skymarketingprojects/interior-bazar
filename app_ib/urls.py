from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from app_ib import views
from rest_framework_simplejwt.views import (TokenRefreshView)
from app_ib.Views import AuthView, QueryView, FeedbackView
from app_ib.Views import ProfileView
# from app_ib.Views.Business import BusinessView
# from app_ib.Views.Business import BusinessLocationView
# from app_ib.Views.Business import BusinessProfileView
# from app_ib.Views import SearchView
from app_ib.Views import PlanQuateView
from app_ib.Views import PlanView
from app_ib.Views import AdsQueryView
from app_ib.Views.Client import ClientLocationView, ClientsView

from app_ib.Views import StockMediaView
from app_ib.Views import BlogView
from app_ib.Views import Subscription
from app_ib.Views import OfferTextView
from app_ib.Views import PaymentView

from app_ib.Views import ContactView
from app_ib.Views import PageView
from .views import generateUploadUrlView

app_name = 'interior_bazzar'
urlpatterns = [
    
    #########################################################
    # Test: 
    #########################################################
    path('test/', views.TestView, name='TestView'),
    path('test-mail/', views.TestMailView, name='TestMailView'),

    #########################################################
    # Authentication: 
    #########################################################
    path('v1/auth/signup/', AuthView.SignupView, name='SignupView'),
    path('v1/auth/signin/', AuthView.LoginView, name='LoginView'),
    path('v1/auth/signout/', AuthView.LogoutView, name='LogoutView'),
    path('v1/auth/delete-account/', AuthView.DeleteAccountView, name='DeleteAccountView'),  
    path('v1/auth/forgot_password_request/', AuthView.ForgotPasswordRequestView, name='ForgotPasswordRequestView'),
    path('v1/auth/forgot-password/<str:hash>/', AuthView.ForgotPasswordView, name='ForgotPasswordView'),
    path('v1/auth/change-password/', AuthView.ChnagePasswordView, name='ChnagePasswordView'),
    path('v1/auth/reset-password/', AuthView.ResetPasswordView, name='ResetPasswordView'),
    
    #########################################################
    # Token: 
    #########################################################
    path('v1/auth/refresh-token/', TokenRefreshView.as_view(), name='token-refresh'),

    #########################################################
    # User Profile: 
    #########################################################
    path('v1/user/profile/create/', ProfileView.CreateProfileView, name='CreateProfileView'),
    path('v1/user/profile-image/update/', ProfileView.CreateOrUpdateProfileImageView, name='CreateOrUpdateProfileImageView'),
    path('v1/user/profile/', ProfileView.GetProfileView, name='GetProfileView'),
    path('v1/user/profile/dashboard/', ProfileView.GetProfileDashbordView, name='GetProfileView'),
    path('v1/user/plan/', ProfileView.GetPlanView, name='GetPlanView'),

    #########################################################
    # Client Location: 
    #########################################################
    path('v1/user/client-location/create-update/', ClientLocationView.CreateOrUpdateClientLocationView, name='CreateOrUpdateClientLocationView'),
    path('v1/user/client-location/<int:id>/', ClientLocationView.GetClientLocationByIDView, name='GetClientLocationByIDView'),


    #########################################################
    # Query: 
    #########################################################
    path('v1/query/', QueryView.GetQueryView, name='GetQueryView'),
    path('v1/query/create/', QueryView.CreateQueryView, name='CreateQueryView'),
    path('v1/query/update/', QueryView.UpdateQueryByIDView, name='UpdateQueryByIDView'),
    path('v1/query/business-queries/', QueryView.GetQueryBusinessView, name='GetQueryBusinessView'),
    path('v1/query/udpate/status/', QueryView.UpdateQueryStatusView, name='UpdateQueryStatusView'),
    path('v1/query/udpate/priority/', QueryView.UpdateQueryPriorityView, name='UpdateQueryPriorityView'),
    path('v1/query/udpate/remark/', QueryView.UpdateQueryRemarkView, name='UpdateQueryPriorityView'),
    #funnel query
    path('v1/query/funnel/create/', QueryView.CreateFunnelQueryView, name='CreateFunnelQueryView'),

    #########################################################
    # Quate: 
    #########################################################
    path('v1/quote/create/', PlanQuateView.CreateQuateView, name='CreateQuateView'),
    path('v1/quote/verify/', PlanQuateView.VerifyQuateView, name='VerifyQuateView'),

    #########################################################
    # Ads Query: 
    #########################################################
    path('v1/query/ads/create/', AdsQueryView.CreateAdsQueryView, name='CreateAdsQueryView'),
    path('v1/query/ads/verify/', AdsQueryView.VerifyAdsQueryView, name='VerifyAdsQueryView'),

  
    #########################################################
    # Feedback: 
    #########################################################
    path('v1/feedback/create/', FeedbackView.CreateFeedbackView, name='CreateFeedbackView'),
    path('v1/feedback/status/update/', FeedbackView.UpdateFeedbackStatusView, name='UpdateFeedbackStatusView'),

    #########################################################
    # Plan: 
    #########################################################
    path('v1/plan/create/',  PlanView.CreatePlanView, name='CreatePlanView'),
    path('v1/plan/verify/', PlanView.VerifyPaymentView, name='VerifyPaymentView'),
    path('v1/plan/template/', Subscription.GetSubscriptionsView, name='GetSubscriptionView'),
 
    #########################################################
    # Contact: 
    #########################################################
    path('v1/contact/create/', ContactView.CreateContactView, name='CreateContactView'),

    #########################################################
    # Pages: 
    #########################################################
    path('v1/page/<str:page_name>/', PageView.GetPagesView, name='PageView'),
    path('v1/qna/', PageView.GetQnAView, name='qna'),

    #########################################################
    # Generate Upload URL: 
    #########################################################
    path('v1/common/get-upload-url/', generateUploadUrlView, name='generateUploadUrlView'),

    #########################################################
    # Stock Media: 
    #########################################################
    path('v1/stock-media/<str:page>/<str:section>/', StockMediaView.GetStockMedia, name='GetStockMediaView'),

    ##########################################################
    # Blog: 
    ##########################################################
    path('v1/blog/', BlogView.GetAllBlogsView, name='GetAllBlogsView'),
    path('v1/blog/pagination/<int:page>/', BlogView.GetBlogsPaginationView, name='GetBlogsPagination'),
    path('v1/blog/<int:id>/', BlogView.GetBlogByIdView, name='GetBlogByTitleView'),

    #########################################################
    # Offer text
    ##########################################################
    path('v1/query/offer-text/', OfferTextView.GetOfferText, name='GetOfferTextView'),

    ######################################################
    # payment gateway
    ######################################################
    path('v1/payment/initiate/', PaymentView.InitiatePaymentView, name='InitiatePaymentView'),
    path('v1/payment/status/', PaymentView.CheckPaymentStatusView, name='CheckPaymentStatusView'),
    path('v1/payment/refund/', PaymentView.RefundTransactionView, name='RefundTransactionView'),

    ######################################################
    # include
    ######################################################
    path('v1/admin/', include('interior_admin.urls')),
    path('v1/ads/', include('interior_ads.urls')),
    path('v1/bots/', include('interior_bot.urls')),
    path('v1/business/', include('interior_business.urls')),
    path('v1/market/', include('interior_products.urls')),
    path('v1/notification/', include('interior_notification.urls')),
]