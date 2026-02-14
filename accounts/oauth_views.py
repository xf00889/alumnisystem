"""
Custom OAuth views with rate limiting for Google SSO.
Wraps django-allauth callback views with rate limiting to prevent abuse.
"""
from django.contrib import messages
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit
from allauth.socialaccount.providers.google.views import oauth2_login, oauth2_callback
import logging

logger = logging.getLogger(__name__)


@require_http_methods(["GET", "POST"])
@ratelimit(key='ip', rate='10/m', method='ALL', block=True)
def google_callback_with_ratelimit(request):
    """
    Google OAuth callback endpoint with rate limiting.
    
    Applies rate limiting of 10 requests per minute per IP address
    to prevent abuse of the OAuth callback endpoint.
    
    If rate limit is exceeded, displays user-friendly error message
    and redirects to login page.
    
    Args:
        request: The HTTP request
        
    Returns:
        Response from allauth callback view or redirect to login
    """
    # Check if request was rate limited
    if getattr(request, 'limited', False):
        logger.warning(
            f"Rate limit exceeded for OAuth callback from IP: {request.META.get('REMOTE_ADDR')}"
        )
        messages.error(
            request,
            "Too many login attempts. Please wait a moment and try again."
        )
        return redirect('account_login')
    
    # Call the original allauth Google OAuth2 callback view
    return oauth2_callback(request)
