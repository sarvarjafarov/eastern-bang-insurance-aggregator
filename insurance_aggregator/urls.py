"""
URL configuration for insurance_aggregator project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.urls import path

from insurance_aggregator import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('product/', views.product, name='product'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('plans/go/<int:plan_id>/', views.plan_redirect, name='plan_redirect'),
    path('contact/', views.contact, name='contact'),
    path('api/traffic/', views.traffic_ingest, name='traffic_ingest'),
    path('ef1ca11/', views.abtest_endpoint, name='abtest_endpoint'),
    path('account/signup/', views.signup_view, name='signup'),
    path('account/login/', views.login_view, name='login'),
    path('account/logout/', views.logout_view, name='logout'),
    path('account/profile/', views.profile_view, name='profile'),
    path('account/deals/', views.deals_list, name='deals_list'),
    path('account/deals/new/', views.deal_create, name='deal_create'),
    path('account/deals/<int:deal_id>/', views.deal_detail, name='deal_detail'),
    path('account/deals/<int:deal_id>/edit/', views.deal_edit, name='deal_edit'),
    path('account/offers/<int:offer_id>/edit/', views.offer_edit, name='offer_edit'),
    path('admin/', admin.site.urls),
]
