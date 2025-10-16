"""
Middleware to redirect users to setup page if setup is not complete.
"""
from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponse
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class SetupRequiredMiddleware:
    """
    Middleware that redirects users to the setup page if the application
    setup is not complete.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # URLs that should be excluded from setup redirect
        self.setup_urls = [
            '/setup/',
            '/admin/',
            '/static/',
            '/media/',
            '/favicon.ico',
        ]
        
        # API endpoints that should be excluded
        self.api_urls = [
            '/api/',
        ]

    def __call__(self, request):
        # Skip setup check for certain paths
        if self._should_skip_setup_check(request):
            return self.get_response(request)
        
        # Check if setup is complete
        if not self._is_setup_complete():
            # Redirect to setup page
            setup_url = reverse('setup:welcome')
            if not request.path.startswith(setup_url):
                logger.info(f"Redirecting to setup page from {request.path}")
                return redirect(setup_url)
        
        return self.get_response(request)

    def _should_skip_setup_check(self, request):
        """
        Determine if setup check should be skipped for this request.
        """
        path = request.path
        
        # Skip for setup URLs
        for setup_url in self.setup_urls:
            if path.startswith(setup_url):
                return True
        
        # Skip for API URLs
        for api_url in self.api_urls:
            if path.startswith(api_url):
                return True
        
        # Skip for static files
        if path.startswith('/static/') or path.startswith('/media/'):
            return True
        
        # Skip for admin if it's a POST request (login, etc.)
        if path.startswith('/admin/') and request.method == 'POST':
            return True
        
        return False

    def _is_setup_complete(self):
        """
        Check if setup is complete.
        """
        try:
            from .utils import is_setup_complete
            return is_setup_complete()
        except Exception as e:
            logger.error(f"Error checking setup status: {e}")
            # If we can't check setup status, assume it's not complete
            return False


class SetupProgressMiddleware:
    """
    Middleware to add setup progress information to request context.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Add setup progress to request
        try:
            from .utils import get_setup_progress
            request.setup_progress = get_setup_progress()
        except Exception as e:
            logger.error(f"Error getting setup progress: {e}")
            request.setup_progress = {
                'environment_setup': False,
                'database_available': False,
                'setup_complete': False,
                'overall_progress': 0
            }
        
        return self.get_response(request)
