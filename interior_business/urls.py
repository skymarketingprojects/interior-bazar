from interior_business.Views import BusinessView, BusinessLocationView, BusinessProfileView,SearchView
from django.urls import path, include

urlpatterns = [

    path('related/<int:businessId>/',SearchView.GetRelatedBusinessView, name='GetRelatedBusinessView'),
    path('nearby/<int:businessId>/',SearchView.GetNearbyBusinessView, name='GetRelatedBusinessView'),
     #########################################################
    # Business:  
    #########################################################
    path('create/', BusinessView.CreateBusinessView, name='CreateBusinessView'),
    path('update/', BusinessView.UpdateBusinessView, name='UpdateBusinessView'),
    path('<int:id>/', BusinessView.GetBusinessByIdView, name='GetBusinessByIdView'),
    path('', BusinessView.GetBusinessByUser, name='GetBusinessByUser'),

    #########################################################
    # Business Location: 
    #########################################################
    path('location/create-update/', BusinessLocationView.CreateOrUpdateBusinessLocationView, name='CreateBusinessLocationView'),
    path('location/<int:id>/', BusinessLocationView.GetBusinessLocationByBussIDView, name='GetBusinessLocationByBussIDView'),


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

    ######################################################
    # location
    ######################################################
    path('location/countries/', BusinessLocationView.GetCountryListView, name='GetCountryListView'),
    path('location/states/<int:countryId>/', BusinessLocationView.GetStateListByCountryIDView, name='GetStateListView'),

    ########################################################
    # Serachview: 
    #########################################################
    path('pagination/<int:index>/', SearchView.GetBusinessByPaginationView, name='GetBusinessByPaginationView'),
    path('top-business/<int:index>/', SearchView.GetTopBusinessView, name='GetTopBusinessView'),
]
