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
        Redirects superusers to admin dashboard, regular users to home.
        """
        if request.user.is_authenticated and request.user.is_superuser:
            return reverse('core:admin_dashboard')
        return reverse('core:home')