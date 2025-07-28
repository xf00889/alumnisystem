from django.urls import path
from . import views
from . import admin_views
from django.views.generic.base import RedirectView

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    
    # Admin Dashboard
    path('admin-dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('api/dashboard-analytics/', admin_views.dashboard_analytics_api, name='dashboard_analytics_api'),

    path('api/engagement-data/', views.engagement_data_api, name='engagement_data_api'),
    path('search/', views.search, name='search'),
    path('go-to-profile/', views.go_to_profile, name='go_to_profile'),
]