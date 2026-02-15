"""
Middleware to ensure Site is always correctly configured for OAuth callbacks
"""
from django.contrib.sites.models import Site
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class EnsureSiteMiddleware:
    """
    Middleware to ensure the current site is always properly configured.
    This fixes issues with OAuth callbacks where the site domain is None.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Ensure the site exists and has the correct domain
        try:
            site_id = getattr(settings, 'SITE_ID', 1)
            site = Site.objects.get(pk=site_id)
            
            # Get the current host from the request
            current_host = request.get_host()
            
            # If the site domain doesn't match the current host, update it
            if site.domain != current_host:
                logger.info(f"Updating site domain from '{site.domain}' to '{current_host}'")
                site.domain = current_host
                site.save(update_fields=['domain'])
        
        except Site.DoesNotExist:
            # Create the site if it doesn't exist
            current_host = request.get_host()
            logger.warning(f"Site with ID {site_id} does not exist. Creating it with domain '{current_host}'")
            Site.objects.create(
                id=site_id,
                domain=current_host,
                name='NORSU Alumni'
            )
        except Exception as e:
            logger.error(f"Error in EnsureSiteMiddleware: {str(e)}")
        
        response = self.get_response(request)
        return response
