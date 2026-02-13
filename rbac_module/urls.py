from django.urls import path
from . import views

urlpatterns = [
    path('roles/', views.RoleCollectionView.as_view(), name='role-collection'),
    path('roles/<int:roleId>/', views.RoleCollectionView.as_view(), name='role-detail'),
    path('roles/<int:roleId>/users/', views.removeUserView, name='role-remove-users'),
    path('roles/<int:roleId>/access/', views.removeAccessView, name='role-remove-access'),
]
