from django.urls import path
from . import admin_views
from .view_handlers.error_handlers import health_check_view
from django.views.generic.base import RedirectView
# Import views directly to avoid conflict with views directory
import core.views as views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),

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

    # Notification API endpoints
    path('api/notifications/', views.get_notifications, name='get_notifications'),
    path('api/notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('api/notifications/unread-count/', views.get_unread_count, name='get_unread_count'),
    
    # Health check endpoint
    path('health/', health_check_view, name='health_check'),
]