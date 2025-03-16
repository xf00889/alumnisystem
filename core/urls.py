from django.urls import path
from . import views
from django.views.generic.base import RedirectView

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('analytics/', RedirectView.as_view(pattern_name='core:admin_dashboard'), name='analytics_dashboard'),
    path('api/engagement-data/', views.engagement_data_api, name='engagement_data_api'),
] 