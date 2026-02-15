"""
Custom middleware for accounts app
"""
from django.conf import settings
from django.contrib.sites.models import Site
import logging

logger = logging.getLogger(__name__)


class EnsureSiteMiddleware:
    """
    Middleware to ensure Site framework is properly configured for OAuth callbacks
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Ensure SITE_ID is set in settings
        if not hasattr(settings, 'SITE_ID'):
            settings.SITE_ID = 1
            logger.warning("SITE_ID not set in settings, defaulting to 1")
        
        # Process the request
        response = self.get_response(request)
        return response
