"""
Middleware for accounts app.
"""
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.urls import reverse, resolve
from django.urls.exceptions import Resolver404


# URLs that incomplete users are allowed to access
REGISTRATION_EXEMPT_URLS = {
    'accounts:post_registration',
    'accounts:cancel_registration',
    'accounts:check_duplicate_alumni',
    'account_logout',
    'account_login',
    'feedback:submit_feedback',
}

# URL path prefixes that are always allowed (static, media, admin, allauth internals)
REGISTRATION_EXEMPT_PREFIXES = (
    '/static/',
    '/media/',
    '/admin/',
    '/accounts/post-registration/',
    '/accounts/cancel-registration/',
    '/accounts/check-duplicate-alumni/',
    '/accounts/logout/',
    '/accounts/login/',
    '/feedback/submit/',
    '/__debug__/',
)


class RegistrationCompleteMiddleware(MiddlewareMixin):
    """
    Redirects authenticated users who have not completed post-registration
    back to the post-registration page.
    Prevents incomplete accounts from accessing any other part of the site.
    """

    def process_request(self, request):
        if not request.user.is_authenticated:
            return None

        # Skip for staff/superusers
        if request.user.is_staff or request.user.is_superuser:
            return None

        # Skip exempt path prefixes
        path = request.path
        if any(path.startswith(prefix) for prefix in REGISTRATION_EXEMPT_PREFIXES):
            return None

        # Check profile completion
        try:
            profile = request.user.profile
            if profile.has_completed_registration:
                return None
        except Exception:
            # No profile — needs to complete registration
            pass

        # Resolve current URL name to check against exempt set
        try:
            match = resolve(path)
            url_name = f"{match.app_name}:{match.url_name}" if match.app_name else match.url_name
            if url_name in REGISTRATION_EXEMPT_URLS:
                return None
        except Resolver404:
            pass

        # Redirect incomplete users to post-registration
        return redirect(reverse('accounts:post_registration'))


class SuppressAuthMessagesMiddleware(MiddlewareMixin):
    """
    Middleware to suppress unwanted authentication messages.
    Removes login/logout success messages that clutter the UI.
    """
    
    def process_request(self, request):
        """
        Process request and filter out unwanted messages BEFORE template rendering.
        This ensures messages are properly consumed and not re-added.
        """
        if hasattr(request, '_messages'):
            storage = messages.get_messages(request)
            
            # Collect messages we want to keep
            messages_to_keep = []
            
            for message in storage:
                message_text = str(message).lower()
                
                # Skip login/logout success messages
                if any(keyword in message_text for keyword in [
                    'signed out',
                    'logged out', 
                    'sign out',
                    'log out',
                    'logout',
                    'signed in',
                    'logged in',
                    'successfully signed in',
                    'successfully logged in'
                ]):
                    continue
                
                # Skip OAuth cancellation and error messages
                if any(keyword in message_text for keyword in [
                    'google sign-in was cancelled',
                    'sign-in was cancelled',
                    'an error occurred during google sign-in',
                    'error occurred during google',
                    'cancelled',
                    'access_denied',
                    'try again or use email/password login'
                ]):
                    continue
                
                # Keep all other messages
                messages_to_keep.append({
                    'level': message.level,
                    'message': message.message,
                    'extra_tags': message.extra_tags
                })
            
            # Messages are now consumed (storage was iterated)
            # Re-add only the filtered messages
            for msg in messages_to_keep:
                messages.add_message(
                    request,
                    msg['level'],
                    msg['message'],
                    extra_tags=msg['extra_tags']
                )
        
        return None
    
    def process_response(self, request, response):
        """
        No longer needed - filtering happens in process_request.
        """
        return response
