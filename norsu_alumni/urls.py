from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.views.static import serve
from django.contrib.auth.decorators import login_required
from accounts import security_views
import os

def profile_search_connected_users(request):
    """Handle old profile API endpoint by calling the accounts API view"""
    from accounts.views import search_connected_users_api
    return search_connected_users_api(request)

urlpatterns = [
    path('admin/', admin.site.urls),
    # CSP Report endpoint for violation monitoring
    path('csp-report/', security_views.csp_report_view, name='csp_report'),
    # Setup URLs - must be before other URLs to catch setup redirects
    path('setup/', include('setup.urls')),
    # Handle old profile API endpoint by calling the accounts API view
    path('profile/api/search-connected-users/', profile_search_connected_users, name='profile_search_connected_users'),
    # Removed redundant signup page - signup is now handled in the tabbed login page
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
]

# Serve media files
if settings.DEBUG:
    # In development, use Django's static file serving
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # In production, serve media files through a view
    def serve_media(request, path):
        """Serve media files in production"""
        # Security: only allow serving files from MEDIA_ROOT
        file_path = os.path.join(settings.MEDIA_ROOT, path)
        
        # Prevent directory traversal attacks
        if not os.path.abspath(file_path).startswith(os.path.abspath(settings.MEDIA_ROOT)):
            raise Http404("File not found")
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise Http404("File not found")
        
        # Serve the file
        return serve(request, path, document_root=settings.MEDIA_ROOT)
    
    urlpatterns += [
        path(f'{settings.MEDIA_URL.strip("/")}/<path:path>', serve_media, name='serve_media'),
    ]
