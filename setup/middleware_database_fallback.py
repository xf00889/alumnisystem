"""
Database fallback middleware for setup process.
"""
import logging
from django.http import JsonResponse
from django.db import connection
from django.conf import settings

logger = logging.getLogger(__name__)


class DatabaseFallbackMiddleware:
    """
    Middleware to handle database unavailability during setup.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if we're in setup mode and database is not ready
        if (request.path.startswith('/setup/') and 
            not self._is_database_ready()):
            
            # For setup pages, we can continue without database
            # The views will handle this gracefully
            logger.info("Database not ready, continuing with setup in fallback mode")
        
        response = self.get_response(request)
        return response
    
    def _is_database_ready(self):
        """Check if database is ready."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            logger.warning(f"Database not ready: {e}")
            return False
