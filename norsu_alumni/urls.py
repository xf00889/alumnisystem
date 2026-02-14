from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponseRedirect, Http404
from django.contrib.sitemaps.views import sitemap
from accounts import security_views
from core.sitemaps import StaticPageSitemap, EventSitemap, JobSitemap
from core import views
import os

# Sitemap configuration
sitemaps = {
    'static': StaticPageSitemap,
    'events': EventSitemap,
    'jobs': JobSitemap,
}

def profile_search_connected_users(request):
    """Handle old profile API endpoint by calling the accounts API view"""
    from accounts.views import search_connected_users_api
    return search_connected_users_api(request)

urlpatterns = [
    # Log viewer - must be before admin to avoid catch-all pattern
    path('admin/logs/', include(('log_viewer.urls', 'log_viewer'), namespace='log_viewer')),
    path('admin/', admin.site.urls),
    # Setup URLs - must be before other URLs to catch setup redirects
    path('setup/', include('setup.urls')),
    # Sitemap
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    # Robots.txt
    path('robots.txt', views.robots_txt, name='robots_txt'),
    # Handle old profile API endpoint by calling the accounts API view
    path('profile/api/search-connected-users/', profile_search_connected_users, name='profile_search_connected_users'),
    # Custom login view with rate limiting (must be before allauth.urls to override)
    path('accounts/login/', security_views.custom_login_view, name='account_login'),
    # Allauth URLs (includes Google OAuth)
    path('accounts/', include('allauth.urls')),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('alumni/', include('alumni_directory.urls')),
    path('groups/', include('alumni_groups.urls')),
    path('connections/', include('connections.urls')),
    path('jobs/', include('jobs.urls')),
    path('location-tracking/', include(('location_tracking.urls', 'location_tracking'), namespace='location_tracking')),
    path('announcements/', include(('announcements.urls', 'announcements'), namespace='announcements')),
    path('events/', include(('events.urls', 'events'), namespace='events')),
    path('feedback/', include(('feedback.urls', 'feedback'), namespace='feedback')),
    path('donations/', include(('donations.urls', 'donations'), namespace='donations')),
    path('mentorship/', include(('mentorship.urls', 'mentorship'), namespace='mentorship')),
    path('surveys/', include(('surveys.urls', 'surveys'), namespace='surveys')),
    path('cms/', include(('cms.urls', 'cms'), namespace='cms')),
    path('docs/', include(('docs.urls', 'docs'), namespace='docs')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Serve media files in production
    from django.views.static import serve
    from django.urls import re_path
    
    def serve_media(request, path):
        """Serve media files in production"""
        document_root = settings.MEDIA_ROOT
        file_path = os.path.join(document_root, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return serve(request, path, document_root=document_root, show_indexes=False)
        raise Http404("Media file not found")
    
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve_media, name='serve_media'),
    ]
