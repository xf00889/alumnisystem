"""
URL configuration for norsu_alumni project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls', namespace='core')),  # Core app URLs including home
    path('accounts/', include('allauth.urls')),  # Django-allauth URLs
    path('profile/', include('accounts.urls', namespace='accounts')),  # Custom user profile URLs
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('announcements/', include('announcements.urls', namespace='announcements')),
    path('alumni-groups/', include('alumni_groups.urls', namespace='alumni_groups')),  # Alumni Groups URLs
    path('alumni-directory/', include('alumni_directory.urls', namespace='alumni_directory')),
    path('events/', include('events.urls', namespace='events')),  # Events app URLs
    path('chat/', include('chat.urls')),  # Add chat URLs
    path('feedback/', include('feedback.urls', namespace='feedback')),  # Feedback app URLs
    path('location/', include('location_tracking.urls', namespace='location_tracking')),  # Location tracking URLs
    path('jobs/', include('jobs.urls', namespace='jobs')),  # Job Board URLs
    path('mentorship/', include('mentorship.urls', namespace='mentorship')),  # Mentorship URLs
    path('api/skills/', include('accounts.urls', namespace='skills')),  # Skill Matching API URLs
    path('surveys/', include('surveys.urls', namespace='surveys')),  # Changed from '' to 'surveys/'
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
