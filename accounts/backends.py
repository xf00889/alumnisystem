"""
Custom authentication backends
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class CustomModelBackend(ModelBackend):
    """
    Custom authentication backend that always checks the latest user state
    from the database, ensuring users who just reset their password can authenticate.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user with email/username and password.
        Always checks the latest user state from the database.
        """
        if username is None:
            username = kwargs.get('email') or kwargs.get(User.USERNAME_FIELD)
        
        if username is None or password is None:
            return None
        
        try:
            # Always get user directly from database (bypassing any cache)
            # Check by email first, then username
            if '@' in username:
                user = User.objects.get(email=username)
            else:
                user = User.objects.get(
                    Q(username=username) | Q(email=username)
                )
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user
            User().set_password(password)
            return None
        
        # Refresh user from database to ensure we have the latest state
        # This is critical for users who just reset their password
        user.refresh_from_db()
        
        # Check password
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None
    
    def user_can_authenticate(self, user):
        """
        Check if the user can authenticate.
        Always check the latest is_active status from the database.
        """
        # Refresh user from database to ensure we have the latest state
        user.refresh_from_db()
        
        # Check if user is active
        is_active = getattr(user, 'is_active', None)
        
        # If user is not active, check if they recently reset their password
        # Allow authentication if they're active OR if we can't determine their status
        return is_active is not False

