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
    path('ef1ca11/click/', views.abtest_click_endpoint, name='abtest_click_endpoint'),
    path('account/signup/', views.signup_view, name='signup'),
    path('account/login/', views.login_view, name='login'),
    path('account/logout/', views.logout_view, name='logout'),
    path('account/profile/', views.profile_view, name='profile'),
    # Packs (with legacy /deals/ aliases)
    path('account/packs/', views.packs_list, name='packs_list'),
    path('account/packs/new/', views.pack_create, name='pack_create'),
    path('account/packs/<int:pack_id>/', views.pack_detail, name='pack_detail'),
    path('account/packs/<int:pack_id>/edit/', views.pack_edit, name='pack_edit'),
    path('account/packs/save/<int:plan_id>/', views.pack_save, name='pack_save'),
    path('account/addons/<int:plan_id>/', views.addons_select, name='addons_select'),
    path('account/reviews/<int:plan_id>/', views.submit_review, name='submit_review'),
    path('account/documents/', views.documents_list, name='documents_list'),
    path('account/notifications/', views.notifications_list, name='notifications_list'),
    path('account/support/', views.support_list, name='support_list'),
    path('account/security/', views.security_view, name='security'),
    path('account/billing/', views.billing_list, name='billing_list'),
    path('account/deals/', views.packs_list, name='deals_list'),
    path('account/deals/new/', views.pack_create, name='deal_create'),
    path('account/deals/<int:pack_id>/', views.pack_detail, name='deal_detail'),
    path('account/deals/<int:pack_id>/edit/', views.pack_edit, name='deal_edit'),
    path('admin/', admin.site.urls),
]
