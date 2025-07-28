from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse

class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter to handle post-login redirection.
    Redirects staff/superusers to admin dashboard, regular users to home.
    """
    
    def get_login_redirect_url(self, request):
        """
        Returns the default URL to redirect to after logging in.
        """
        # Always redirect to home page, which will handle the appropriate display
        # This prevents redirect loops and provides consistent behavior
        return reverse('core:home')