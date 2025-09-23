"""
URL configuration for interior_bazzar project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

from app_ib.views import TestView
from django.contrib.sitemaps.views import sitemap
from .sitemaps import StaticPageSitemap, BlogPostSitemap
from . import views
sitemaps = {
    'static': StaticPageSitemap,
    'blog': BlogPostSitemap,
}


urlpatterns = [
    path('',TestView, name='test'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('terms-of-use/', admin.site.urls),
    path('api/', include("app_ib.urls")),
     path('seller-buyer/', views.seller_buyer, name='seller_buyer'),
    path('blog/', views.blog, name='blog'),
    path('blog/<slug:slug>/', views.blog_detail, name='blog_detail'),  # For individual blog posts
    path('plan/', views.plan, name='plan'),
    path('faqs/', views.faqs, name='faqs'),
    path('disclaimer/', views.disclaimer, name='disclaimer'),
    path('return-and-refund-policy/', views.return_and_refund_policy, name='return_and_refund_policy'),
    path('terms-and-conditions/', views.terms_and_conditions, name='terms_and_conditions'),
    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('sign-up/', views.sign_up, name='sign_up'),
    path('sign-in/', views.sign_in, name='sign_in'),
    path('contact-us/', views.contact_us, name='contact_us'),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, documents_root=settings.MEDIA_ROOT)
