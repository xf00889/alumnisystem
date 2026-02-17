from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.core.files.base import ContentFile
from django.shortcuts import redirect
from allauth.socialaccount.models import SocialLogin
import requests
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter to handle post-login redirection.
    Redirects staff/superusers to admin dashboard, regular users to home.
    """
    
    def get_login_redirect_url(self, request):
        """
        Returns the default URL to redirect to after logging in.
        Redirects superusers to admin dashboard.
        Checks if user has completed post-registration, if not redirects to post-registration.
        Otherwise redirects to home.
        """
        # Superusers and staff should always go to admin dashboard, regardless of profile completion
        if request.user.is_authenticated and (request.user.is_superuser or request.user.is_staff):
            return reverse('core:admin_dashboard')
        
        # Check if user has completed post-registration
        try:
            profile = request.user.profile
            if not profile.has_completed_registration:
                return reverse('accounts:post_registration')
        except:
            # Profile doesn't exist or error - redirect to post-registration to create it
            return reverse('accounts:post_registration')
        
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
        Also validates reCAPTCHA if enabled.
        This method is called before authentication, allowing us to refresh
        the user from the database to get the latest is_active status.
        """
        # Validate reCAPTCHA if enabled
        from core.recaptcha_utils import is_recaptcha_enabled, get_recaptcha_config
        if is_recaptcha_enabled():
            recaptcha_token = request.POST.get('g-recaptcha-response')
            if recaptcha_token:
                config = get_recaptcha_config()
                if config:
                    try:
                        result = config.verify_token(recaptcha_token)
                        if not result.get('success', False):
                            logger.warning(f"reCAPTCHA validation failed for login attempt")
                            # Don't block login, just log it
                    except Exception as e:
                        logger.error(f"reCAPTCHA verification error: {e}")
                        # Don't block login if verification fails
        
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
    
    def is_open_for_signup(self, request):
        """
        Check if signup is open - always return True to allow signups.
        """
        return True
    
    def can_authenticate(self, user):
        """
        Override to allow authentication if user is active.
        This is called AFTER authentication but before redirecting.
        We refresh the user from DB to get the latest state.
        """
        if user:
            # Always refresh from database to get latest state
            user.refresh_from_db()
            # Return True if user is active, False otherwise
            return user.is_active
        return False
    
    def respond_user_inactive(self, request, user):
        """
        Handle inactive user login attempt by redirecting to email verification page.
        This ensures users who haven't verified their email complete the verification process.
        """
        from django.shortcuts import redirect
        from django.contrib import messages
        
        # Store the user's email in session for resend verification
        request.session['inactive_account_email'] = user.email
        
        # Add informative message
        messages.warning(
            request,
            'Your email address has not been verified yet. Please enter the verification code sent to your email, or request a new one.'
        )
        
        # Log the inactive login attempt
        logger.info(f"Inactive user login attempt: {user.email} - redirecting to email verification")
        
        # Redirect to email verification page with email parameter
        return redirect(f'/accounts/verify-email/?email={user.email}')
    
    def add_message(self, request, level, message_tag, message=None, extra_tags='', *args, **kwargs):
        """
        Override to suppress logout success message.
        We don't want to show "You have signed out" message when user visits login page later.
        
        Note: In some allauth versions, 'message' might be passed as a keyword argument.
        """
        # Suppress ALL logout-related messages by tag
        if message_tag in ['account_logout', 'logged_out', 'signed_out', 'account_logged_out']:
            return
        
        # Check if message is a string before checking for logout-related text
        # (message can be a dict for i18n in some allauth versions)
        if message and isinstance(message, str):
            message_lower = message.lower()
            # Suppress any message containing logout/signout related text
            if any(keyword in message_lower for keyword in ['signed out', 'logged out', 'sign out', 'log out', 'logout', 'signed-out']):
                return
        
        # Also check if message is a lazy translation object
        if message:
            try:
                message_str = str(message).lower()
                if any(keyword in message_str for keyword in ['signed out', 'logged out', 'sign out', 'log out', 'logout', 'signed-out']):
                    return
            except:
                pass
        
        # Call parent method for all other messages
        if message is not None:
            return super().add_message(request, level, message_tag, message, extra_tags, *args, **kwargs)
        else:
            # If message is None, call parent without it (let parent handle default)
            return super().add_message(request, level, message_tag, extra_tags=extra_tags, *args, **kwargs)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom social account adapter to handle social login behavior.
    Automatically verifies email addresses from trusted providers (Google, Facebook).
    Handles account linking, profile creation, and avatar download for Google SSO.
    Includes comprehensive error handling for OAuth failures, network errors, and configuration issues.
    """
    
    def is_auto_signup_allowed(self, request, sociallogin):
        """
        Allow automatic signup for social accounts without additional confirmation.
        This skips the intermediate signup form.
        """
        return True
    
    def get_signup_redirect_url(self, request):
        """
        Redirect SSO signups to post-registration page to complete profile.
        """
        try:
            return reverse('accounts:post_registration')
        except Exception as e:
            logger.error(f"Error in get_signup_redirect_url: {str(e)}")
            return reverse('core:home')
    
    def get_login_redirect_url(self, request):
        """
        Returns the default URL to redirect to after social login.
        Checks if user has completed post-registration, if not redirects there.
        """
        try:
            if request.user.is_authenticated:
                # Superusers and staff should always go to admin dashboard
                if request.user.is_superuser or request.user.is_staff:
                    return reverse('core:admin_dashboard')
                
                # Check if user has completed post-registration
                try:
                    profile = request.user.profile
                    if not profile.has_completed_registration:
                        return reverse('accounts:post_registration')
                except Exception as profile_error:
                    # Profile doesn't exist - redirect to post-registration
                    logger.warning(f"Profile not found for user {request.user.email}: {str(profile_error)}")
                    return reverse('accounts:post_registration')
            
            return reverse('core:home')
        except Exception as e:
            logger.error(f"Error in get_login_redirect_url: {str(e)}")
            return reverse('core:home')
    
    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        """
        Handle OAuth authentication errors from social providers.
        Provides user-friendly error messages and logs detailed errors for administrators.
        
        Args:
            request: The HTTP request
            provider_id: The social provider ID (e.g., 'google')
            error: Error code or type
            exception: Exception object if available
            extra_context: Additional context about the error
        """
        # Log detailed error for administrator review
        error_details = {
            'provider': provider_id,
            'error': str(error) if error else 'Unknown error',
            'exception': str(exception) if exception else None,
            'extra_context': extra_context,
            'user_ip': request.META.get('REMOTE_ADDR'),
            'user_agent': request.META.get('HTTP_USER_AGENT'),
        }
        logger.error(f"OAuth authentication error: {error_details}")
        
        # Determine user-friendly message based on error type
        if error == 'access_denied' or (exception and 'access_denied' in str(exception).lower()):
            # User cancelled the OAuth flow
            messages.info(
                request,
                "Google sign-in was cancelled. You can try again or use email/password login."
            )
        elif error == 'invalid_client' or (exception and 'invalid_client' in str(exception).lower()):
            # OAuth credentials misconfigured
            messages.error(
                request,
                "Google sign-in is temporarily unavailable. Please use email/password login or contact support."
            )
            logger.critical(f"OAuth credentials misconfigured for provider {provider_id}")
        elif error == 'server_error' or (exception and 'server_error' in str(exception).lower()):
            # Google's server error
            messages.error(
                request,
                "Google is experiencing technical difficulties. Please try again in a few moments."
            )
        elif exception and isinstance(exception, requests.exceptions.Timeout):
            # Network timeout
            messages.error(
                request,
                "Connection to Google timed out. Please check your internet connection and try again."
            )
        elif exception and isinstance(exception, (requests.exceptions.ConnectionError, requests.exceptions.RequestException)):
            # Network errors
            messages.error(
                request,
                "Unable to connect to Google. Please check your internet connection and try again."
            )
        else:
            # Generic error
            messages.error(
                request,
                "An error occurred during Google sign-in. Please try again or use email/password login."
            )
        
        # Redirect to login page
        return redirect('account_login')
    
    def populate_user(self, request, sociallogin, data):
        """
        Populate user instance with data from social provider.
        Map Google profile data to User fields (first_name, last_name, email).
        Mark email as verified since it comes from trusted provider.
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Map Google profile data to User fields
        if sociallogin.account.provider == 'google':
            # Google provides 'given_name' and 'family_name'
            extra_data = sociallogin.account.extra_data
            user.first_name = extra_data.get('given_name', '')
            user.last_name = extra_data.get('family_name', '')
            
            # Ensure email is set
            if not user.email and data.get('email'):
                user.email = data.get('email')
        
        # Social providers (Google, Facebook) already verify emails
        # So we can trust the email address
        if sociallogin.account.provider in ['google', 'facebook']:
            user.email_verified = True
        
        return user
    
    def save_user(self, request, sociallogin, form=None):
        """
        Save the user and create associated Profile.
        Download and set Google profile picture as avatar.
        Mark email as verified for social logins.
        Includes comprehensive error handling for profile creation and avatar download.
        """
        user = super().save_user(request, sociallogin, form)
        
        profile_created = False
        
        try:
            # Track SSO usage
            try:
                from core.models import SSOConfig
                provider_config = SSOConfig.get_provider_config_by_type(sociallogin.account.provider)
                if provider_config:
                    provider_config.increment_usage()
            except Exception as e:
                logger.warning(f"Failed to track SSO usage: {str(e)}")
            
            # Mark email as verified for trusted social providers
            if sociallogin.account.provider in ['google', 'facebook']:
                # Get or create email address record
                from allauth.account.models import EmailAddress
                email_address, created = EmailAddress.objects.get_or_create(
                    user=user,
                    email=user.email.lower(),
                    defaults={'verified': True, 'primary': True}
                )
                
                # If it already exists, update it
                if not created:
                    email_address.verified = True
                    email_address.primary = True
                    email_address.save()
            
            # Create Profile if it doesn't exist (for new users)
            from accounts.models import Profile
            profile, profile_created = Profile.objects.get_or_create(user=user)
            
            # For new SSO signups, ensure has_completed_registration is False
            # so they are redirected to post-registration
            if profile_created:
                profile.has_completed_registration = False
                profile.save()
                logger.info(f"Created new profile for SSO user {user.email}, needs to complete registration")
            
            # Download and set Google avatar for new profiles or profiles without avatar
            if sociallogin.account.provider == 'google' and (profile_created or not profile.avatar):
                extra_data = sociallogin.account.extra_data
                picture_url = extra_data.get('picture')
                
                if picture_url:
                    try:
                        # Download the profile picture with timeout
                        response = requests.get(picture_url, timeout=10)
                        response.raise_for_status()
                        
                        # Save the image to the profile
                        image_name = f"google_avatar_{user.id}.jpg"
                        profile.avatar.save(
                            image_name,
                            ContentFile(response.content),
                            save=True
                        )
                        logger.info(f"Successfully downloaded Google avatar for user {user.email}")
                    except requests.exceptions.Timeout:
                        # Network timeout - log but don't fail
                        logger.warning(f"Timeout downloading Google avatar for user {user.email}")
                    except requests.exceptions.ConnectionError:
                        # Connection error - log but don't fail
                        logger.warning(f"Connection error downloading Google avatar for user {user.email}")
                    except requests.exceptions.RequestException as e:
                        # Other request errors - log but don't fail
                        logger.warning(f"Failed to download Google avatar for user {user.email}: {str(e)}")
                    except Exception as e:
                        # Unexpected errors - log with full traceback
                        logger.error(f"Unexpected error downloading Google avatar for user {user.email}: {str(e)}", exc_info=True)
            
            # Add success message for first-time Google sign-ins
            if profile_created:
                messages.success(request, "Welcome! Your account has been created successfully.")
        
        except Exception as e:
            # Log error but don't fail the entire authentication process
            logger.error(f"Error in save_user for social login: {str(e)}", exc_info=True)
            messages.warning(request, "Your account was created, but there was an issue setting up your profile. Please update your profile information.")
        
        return user
    
    def pre_social_login(self, request, sociallogin):
        """
        Handle existing users who try to login with social account.
        If email already exists, check if it's already linked to a different social account.
        If not linked, connect the social account to existing user.
        This enables account linking for users with matching emails.
        Includes comprehensive error handling and user notifications.
        """
        try:
            # If user is already logged in, just connect the account
            if request.user.is_authenticated:
                return
            
            # Check if this social account is already connected
            if sociallogin.is_existing:
                return
            
            # Check if email already exists in the system
            if sociallogin.email_addresses:
                email = sociallogin.email_addresses[0].email.lower()
                try:
                    # Find existing user with this email
                    existing_user = User.objects.get(email=email)
                    
                    # Check if this user already has a Google account linked
                    from allauth.socialaccount.models import SocialAccount
                    existing_google_account = SocialAccount.objects.filter(
                        user=existing_user,
                        provider='google'
                    ).first()
                    
                    if existing_google_account:
                        # User already has a Google account linked
                        google_email = existing_google_account.extra_data.get('email', 'unknown')
                        
                        # Check if it's the same Google account
                        if existing_google_account.uid == sociallogin.account.uid:
                            # Same Google account, just log them in
                            logger.info(f"User {email} logging in with existing Google account")
                        else:
                            # Different Google account trying to link to same email
                            logger.warning(
                                f"Attempt to link different Google account to user {email}. "
                                f"Existing: {google_email}, New: {sociallogin.account.extra_data.get('email')}"
                            )
                            messages.error(
                                request,
                                f"This email address ({email}) is already associated with a different Google account ({google_email}). "
                                f"Please sign in with that Google account or use email/password login."
                            )
                            # Prevent the login by raising an exception
                            from allauth.core.exceptions import ImmediateHttpResponse
                            raise ImmediateHttpResponse(redirect('account_login'))
                    else:
                        # No Google account linked yet, connect this one
                        sociallogin.connect(request, existing_user)
                        
                        # Add informational message
                        messages.success(
                            request,
                            f"Your Google account has been successfully linked to your existing account. "
                            f"You can now sign in using either Google or your email/password."
                        )
                        
                        logger.info(f"Linked Google account to existing user: {email}")
                    
                except User.DoesNotExist:
                    # No existing user, will create new one
                    logger.info(f"Creating new user for Google account: {email}")
                    pass
                except User.MultipleObjectsReturned:
                    # Multiple users with same email (shouldn't happen with unique constraint)
                    logger.error(f"Multiple users found with email: {email}")
                    messages.error(
                        request,
                        "There was an issue with your account. Please contact support."
                    )
                    from allauth.core.exceptions import ImmediateHttpResponse
                    raise ImmediateHttpResponse(redirect('account_login'))
                except Exception as e:
                    # Log any other errors but don't block the authentication
                    logger.error(f"Error linking social account: {str(e)}", exc_info=True)
                    messages.error(
                        request,
                        "There was an issue processing your login. Please try again."
                    )
        except Exception as e:
            # Catch-all for any unexpected errors in pre_social_login
            logger.error(f"Unexpected error in pre_social_login: {str(e)}", exc_info=True)
            messages.error(
                request,
                "An unexpected error occurred. Please try again or contact support."
            )
