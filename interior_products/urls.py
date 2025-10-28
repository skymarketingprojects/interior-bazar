from django.urls import path, include
from . import views

app_name = 'interior_products'

urlpatterns = [
    # path('catalogue/create/',views.CreateCatelogView, name='create_catelog'),
    # path('catalogue/<int:catelogueId>/update/',views.UpdateCatelogView, name='update_catelog'),
    # path('catalogue/<businessId>/',views.GetCatelogView, name='get_catelog'),
    # path('catalogue/<int:catelogueId>/delete/',views.DeleteCatelogView, name='delete_catelog'),
    path('catalogue/',views.CatelogView.as_view()),
    path('catalogue/<int:catelogueId>/',views.CatelogView.as_view()),
    path('catalogue/business/<int:businessId>/',views.GetBusinessCatelogs, name='get_catelog'),

    #products
    path('product/',views.ProductView.as_view()),
    path('product/<int:productId>/',views.ProductView.as_view()),
    path('product/business/<int:businessId>/',views.GetBusinessProducts, name='get_products'),
    #service
    path('service/',views.ServiceView.as_view()),
    path('service/<int:serviceId>/',views.ServiceView.as_view()),
    path('service/business/<int:businessId>/',views.GetBusinessServices, name='get_Services'),
]
