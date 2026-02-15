"""
Custom provider configurations to fix callback URL issues
"""
from allauth.socialaccount.providers.google.provider import GoogleProvider as BaseGoogleProvider


class GoogleProvider(BaseGoogleProvider):
    """
    Custom Google provider that fixes callback URL generation
    """
    
    def get_callback_url(self, request, app):
        """
        Override to ensure callback URL doesn't have /None appended
        """
        # Use the standard callback URL without any process parameter
        callback_url = super().get_callback_url(request, app)
        
        # Remove any /None suffix if present
        if callback_url and callback_url.endswith('/None'):
            callback_url = callback_url[:-5]  # Remove '/None'
        
        return callback_url


provider_classes = [GoogleProvider]
