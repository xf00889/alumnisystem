"""
URL configuration for the setup app.
"""
from django.urls import path
from . import views

app_name = 'setup'

urlpatterns = [
    # Simplified setup flow - only superuser creation
    path('', views.SetupWelcomeView.as_view(), name='welcome'),
    path('admin-setup/', views.SuperuserSetupView.as_view(), name='superuser_setup'),
    path('complete/', views.SetupCompleteView.as_view(), name='complete'),
]
