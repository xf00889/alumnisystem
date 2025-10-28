from django.urls import path
from . import admin_views
from . import smtp_admin_views
from . import recaptcha_admin_views, recaptcha_analytics_views
from .view_handlers.error_handlers import health_check_view
from django.views.generic.base import RedirectView
# Import views directly from views.py file to avoid conflict with views directory
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('superuser/', views.SuperuserCreationView.as_view(), name='create_superuser'),  # One-time superuser creation

    # Landing Page URLs for unauthenticated users
    path('landing/events/', views.landing_events, name='landing_events'),
    path('landing/announcements/', views.landing_announcements, name='landing_announcements'),
    path('news/', views.landing_news, name='landing_news'),
    path('about-us/', views.about_us, name='about_us'),
    path('contact-us/', views.contact_us, name='contact_us'),
    path('contact-us/submit/', views.contact_us_submit, name='contact_us_submit'),

    # Admin Dashboard
    path('admin-dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('api/dashboard-analytics/', admin_views.dashboard_analytics_api, name='dashboard_analytics_api'),
    path('api/alumni-by-college/', admin_views.alumni_by_college_api, name='alumni_by_college_api'),

    # Export URLs
    path('export/alumni/<str:format_type>/', admin_views.export_alumni, name='export_alumni'),
    path('export/jobs/<str:format_type>/', admin_views.export_jobs, name='export_jobs'),
    path('export/mentorships/<str:format_type>/', admin_views.export_mentorships, name='export_mentorships'),
    path('export/events/<str:format_type>/', admin_views.export_events, name='export_events'),
    path('export/donations/<str:format_type>/', admin_views.export_donations, name='export_donations'),
    path('export/users/<str:format_type>/', admin_views.export_users, name='export_users'),
    path('export/announcements/<str:format_type>/', admin_views.export_announcements, name='export_announcements'),
    path('export/feedback/<str:format_type>/', admin_views.export_feedback, name='export_feedback'),
    path('export/surveys/<str:format_type>/', admin_views.export_surveys, name='export_surveys'),
    path('export/all/<str:format_type>/', admin_views.export_all_data, name='export_all_data'),
    
    # Bulk Export URLs
    path('bulk-export/', admin_views.bulk_export_interface, name='bulk_export_interface'),
    path('bulk-export/process/', admin_views.bulk_export_process, name='bulk_export_process'),


    path('api/engagement-data/', views.engagement_data_api, name='engagement_data_api'),
    path('search/', views.search, name='search'),
    path('go-to-profile/', views.go_to_profile, name='go_to_profile'),
    path('test-recaptcha/', views.test_recaptcha, name='test_recaptcha'),

    # Notification API endpoints
    path('api/notifications/', views.get_notifications, name='get_notifications'),
    path('api/notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('api/notifications/unread-count/', views.get_unread_count, name='get_unread_count'),
    
    # Health check endpoint
    path('health/', health_check_view, name='health_check'),
    
    # SMTP Configuration URLs
    path('admin-dashboard/smtp/', smtp_admin_views.smtp_configuration_list, name='smtp_configuration_list'),
    path('admin-dashboard/smtp/create/', smtp_admin_views.smtp_configuration_create, name='smtp_configuration_create'),
    path('admin-dashboard/smtp/quick-setup/', smtp_admin_views.smtp_quick_setup, name='smtp_quick_setup'),
    path('admin-dashboard/smtp/<int:config_id>/edit/', smtp_admin_views.smtp_configuration_edit, name='smtp_configuration_edit'),
    path('admin-dashboard/smtp/<int:config_id>/test/', smtp_admin_views.smtp_configuration_test, name='smtp_configuration_test'),
    path('admin-dashboard/smtp/<int:config_id>/delete/', smtp_admin_views.smtp_configuration_delete, name='smtp_configuration_delete'),
    path('admin-dashboard/smtp/<int:config_id>/activate/', smtp_admin_views.smtp_configuration_activate, name='smtp_configuration_activate'),
    
    # Brevo Configuration URLs
    path('admin-dashboard/brevo/<int:config_id>/test/', smtp_admin_views.brevo_configuration_test, name='brevo_configuration_test'),
    path('admin-dashboard/brevo/<int:config_id>/activate/', smtp_admin_views.brevo_configuration_activate, name='brevo_configuration_activate'),
    path('admin-dashboard/brevo/<int:config_id>/delete/', smtp_admin_views.brevo_configuration_delete, name='brevo_configuration_delete'),
    
    # reCAPTCHA Configuration URLs
    path('admin-dashboard/recaptcha/', recaptcha_admin_views.recaptcha_configuration_list, name='recaptcha_configuration_list'),
    path('admin-dashboard/recaptcha/create/', recaptcha_admin_views.recaptcha_configuration_create, name='recaptcha_configuration_create'),
    path('admin-dashboard/recaptcha/<int:config_id>/edit/', recaptcha_admin_views.recaptcha_configuration_edit, name='recaptcha_configuration_edit'),
    path('admin-dashboard/recaptcha/<int:config_id>/test/', recaptcha_admin_views.recaptcha_configuration_test, name='recaptcha_configuration_test'),
    path('admin-dashboard/recaptcha/<int:config_id>/delete/', recaptcha_admin_views.recaptcha_configuration_delete, name='recaptcha_configuration_delete'),
    path('admin-dashboard/recaptcha/<int:config_id>/activate/', recaptcha_admin_views.recaptcha_configuration_activate, name='recaptcha_configuration_activate'),
    path('admin-dashboard/recaptcha/<int:config_id>/toggle-enabled/', recaptcha_admin_views.recaptcha_configuration_toggle_enabled, name='recaptcha_configuration_toggle_enabled'),
    
    # reCAPTCHA Analytics URLs
    path('admin-dashboard/recaptcha/analytics/', recaptcha_analytics_views.ReCaptchaAnalyticsView.as_view(), name='recaptcha_analytics'),
    path('admin-dashboard/recaptcha/analytics/api/', recaptcha_analytics_views.recaptcha_analytics_api, name='recaptcha_analytics_api'),
    path('admin-dashboard/recaptcha/analytics/reset/', recaptcha_analytics_views.recaptcha_analytics_reset, name='recaptcha_analytics_reset'),
]