"""
URL configuration for the setup app.
"""
from django.urls import path
from . import views
from . import views_migration
from . import api_views

app_name = 'setup'

urlpatterns = [
    # Migration runner (should be first)
    path('migrate/', views_migration.MigrationRunnerView.as_view(), name='migration_runner'),
    path('api/database-status/', views_migration.DatabaseStatusAPIView.as_view(), name='database_status'),
    
    # Setup flow URLs
    path('', views.SetupWelcomeView.as_view(), name='welcome'),
    path('basic-config/', views.BasicConfigView.as_view(), name='basic_config'),
    path('email-config/', views.EmailConfigView.as_view(), name='email_config'),
    path('superuser-setup/', views.SuperuserSetupView.as_view(), name='superuser_setup'),
    path('complete/', views.SetupCompleteView.as_view(), name='complete'),
    path('progress/', views.SetupProgressView.as_view(), name='progress'),
    
    # API endpoints for AJAX requests
    path('api/test-email/', api_views.TestEmailAPIView.as_view(), name='test_email'),
    path('api/check-database/', api_views.CheckDatabaseAPIView.as_view(), name='check_database'),
    path('api/progress/', api_views.SetupProgressAPIView.as_view(), name='api_progress'),
    path('api/site-config/', api_views.SiteConfigurationAPIView.as_view(), name='api_site_config'),
    path('api/email-config/', api_views.EmailConfigurationAPIView.as_view(), name='api_email_config'),
    path('api/feature-toggles/', api_views.FeatureToggleAPIView.as_view(), name='api_feature_toggles'),
]
