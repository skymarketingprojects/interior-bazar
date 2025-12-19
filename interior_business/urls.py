from interior_business.Views import BusinessView, BusinessLocationView, BusinessProfileView,SearchView,BusinessScheduleViews
from django.urls import path, include
from . import views
urlpatterns = [


    path('related/<int:businessId>/',SearchView.GetRelatedBusinessView, name='GetRelatedBusinessView'),
    path('nearby/',SearchView.GetNearbyBusinessView, name='GetAllNearbyBusinessView'),
    path('nearby/<int:businessId>/',SearchView.GetNearbyBusinessView, name='GetnearbyBusinessView'),
     #########################################################
    # Business:  
    #########################################################
    path('detail//header/<int:businessId>/',BusinessView.GetBusinessHeaderView, name='GetBusinessHeaderView'),
    path('create/', BusinessView.CreateBusinessView, name='CreateBusinessView'),
    path('update/', BusinessView.UpdateBusinessView, name='UpdateBusinessView'),
    path('<int:id>/', BusinessView.GetBusinessByIdView, name='GetBusinessByIdView'),
    path('', BusinessView.GetBusinessByUser, name='GetBusinessByUser'),

    #########################################################
    # Business Location:
    #########################################################
    path('location/create-update/', BusinessLocationView.CreateOrUpdateBusinessLocationView, name='CreateBusinessLocationView'),
    path('location/', BusinessLocationView.GetBusinessLocationView, name='GetBusinessLocationByBussIDView'),


    #########################################################
    # Business Profile: 
    #########################################################

    path('profile/create-update/', BusinessProfileView.CreateOrUpdateBusinessProfileView, name='CreateOrUpdateBusinessProfileView'),
    path('profile/<int:id>/', BusinessProfileView.GetBusinessProfileByBussIDView, name='GetBusinessProfileByBussIDView'),
    path('primary-image/create-or-update/', BusinessProfileView.CreateOrUpdatePrimaryImageView, name='CreateOrUpdateProfileImageView'),
    path('secondary-image/create-or-update/', BusinessProfileView.CreateOrUpdateSecondaryImageView, name='CreateOrUpdateSecondaryImageView'),

    ##########################################################
    # business type, category, segment
    ##########################################################
    path('types/', BusinessView.GetAllBusinessTypesView, name='GetAllBusinessTypes'),
    path('categories/', BusinessView.GetAllBusinessCategoriesView, name='GetAllBusinessCategories'),
    path('segments/<int:typeId>/', BusinessView.GetAllBusinessSegmentsByTypeView, name='GetBusinessSegmentsByCategory'),
    path('tab/', BusinessView.GetAllBusinessTabView, name='GetAllBusinessTab'),
    path('explore/', BusinessView.GetExploreSectionsView, name='exploreSection'),

    ######################################################
    # location
    ######################################################
    path('location/countries/', BusinessLocationView.GetCountryListView, name='GetCountryListView'),
    path('location/states/<int:countryId>/', BusinessLocationView.GetStateListByCountryIDView, name='GetStateListView'),

    ########################################################
    # Serachview: 
    #########################################################
    path('pagination/', SearchView.GetBusinessByPaginationView, name='GetBusinessByPaginationView'),
    path('top-business/<int:index>/', SearchView.GetTopBusinessView, name='GetTopBusinessView'),
    
    #########################################################
    # Business Social Media: 
    #########################################################
    path('social-media/', views.BusinessSocialMediaAPIView.as_view(), name='create_bsm'),
    path('social-media/<int:businessId>/', views.BusinessSocialMediaAPIView.as_view()),
    path('social-media/get', views.GetSocialMediaListView, name='get_social_media_list'),

    ##########################################################
    # Business Detail: 
    ##########################################################
    path('detail/header/<int:businessId>/', BusinessProfileView.GetBusinessProfileForDisplayView, name='GetBusinessProfileForDisplayView'),
    path('detail/header/', BusinessProfileView.GetBusinessProfileForDisplayView, name='GetBusinessProfileForDisplayView'),
    path('detail/contact/<int:businessId>/', views.GetContactView, name='GetBusinesscontact'),

    ###########################################################
    # Business Schedule: 
    ##########################################################
    path('working-hours/', BusinessScheduleViews.BusinessScheduleView.as_view()),

    ###########################################################
    # Business Banner :
    ##########################################################
    path('banner/',BusinessView.BusinessBannerView.as_view()),
]
