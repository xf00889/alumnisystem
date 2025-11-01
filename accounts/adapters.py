from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

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
    
    def get_signup_redirect_url(self, request):
        """
        Override signup redirect to prevent allauth from interfering with our custom signup flow.
        Return None to let our custom view handle the redirect.
        """
        return None
    
    def pre_authenticate(self, request, **credentials):
        """
        Override to ensure users who just reset their password can authenticate.
        This method is called before authentication, allowing us to refresh
        the user from the database to get the latest is_active status.
        """
        email = credentials.get('email')
        
        if email:
            try:
                # Get user directly from database (bypassing any cache)
                user = User.objects.get(email=email)
                # Refresh to ensure we have the latest state
                user.refresh_from_db()
            except User.DoesNotExist:
                pass
        
        # Call parent method for default behavior
        return super().pre_authenticate(request, **credentials)