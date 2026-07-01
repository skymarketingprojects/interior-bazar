from django.urls import path, include
from . import views
from . import v3Views

app_name = 'interior_products'

urlpatterns = [
    # CatelogView (class-based) handles GET/POST/PUT/DELETE for the authed user's OWN
    # business (ownership-gated in DeleteCatelog/UpdateCatelog). The legacy per-verb
    # function views (CreateCatelogView/DeleteCatelogView…) are superseded by it.
    # NOTE: No cache here — returns data for the authenticated user's OWN business
    path('catalogue/', views.CatelogView.as_view()),
    path('catalogue/<int:catelogueId>/', views.CatelogView.as_view()),
    path('catalogue/business/<int:businessId>/', views.GetBusinessCatelogs, name='get_catelog'),
    path('catalogue/<int:catelogId>/related/', views.GetRelatedCatelogs, name='related_catelog'),
    path('catalogue/all/', views.GetAllCatelogsView, name='related_catelog'),

    #products
    # NOTE: No cache here — returns data for the authenticated user's OWN business
    path('product/', views.ProductView.as_view()),
    path('product/<int:productId>/', views.ProductView.as_view()),
    path('product/business/<int:businessId>/', views.GetBusinessProducts, name='get_products'),
    path('product/<int:productId>/related/', views.GetRelatedProducts, name='related_products'),
    path('product/all/', views.GetAllProductView, name='related_catelog'),
    #service
    # NOTE: No cache here — returns data for the authenticated user's OWN business
    path('service/', views.ServiceView.as_view()),
    path('service/<int:serviceId>/', views.ServiceView.as_view()),
    path('service/business/<int:businessId>/', views.GetBusinessServices, name='get_Services'),
    path('service/<int:serviceId>/related/', views.GetRelatedServices, name='related_Services'),
    path('service/all/', views.GetAllServiceView, name='related_catelog'),

    # categories
    path('category/', views.GetProductCategoriesView, name="get_categories"),
    path('sub-category/', views.GetProductSubCategoriesView, name="get_sub_categories"),

    #tab
    path('tab/', views.GetTabsView, name="get_tabs"),
    path('own-services/', views.GetOwnServicesView, name="own_services"),

    # ── v3 product detail flow (NEW, additive — legacy endpoints above are frozen) ──
    # Redis-free reads consumed only by the v3 frontend; see v3Views.py.
    # NOTE: the two fixed-suffix routes must stay above the <str:slugOrId> catch-all.
    path('v3/product/<int:productId>/related/', v3Views.RelatedProductsV3View.as_view(), name='ProductRelatedV3'),
    path('v3/product/<int:productId>/from-business/', v3Views.BusinessProductsV3View.as_view(), name='ProductFromBusinessV3'),
    path('v3/product/<str:slugOrId>/', v3Views.ProductDetailV3View.as_view(), name='ProductDetailV3'),

]
