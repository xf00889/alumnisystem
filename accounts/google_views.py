"""
Custom Google OAuth views that fix the callback URL issue
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.views import OAuth2LoginView, OAuth2CallbackView
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.shortcuts import get_current_site
import logging

logger = logging.getLogger(__name__)


class FixedGoogleOAuth2Adapter(GoogleOAuth2Adapter):
    """
    Custom Google OAuth2 adapter that fixes callback URL generation
    """
    
    def get_callback_url(self, request, app):
        """
        Override to fix the /None issue in callback URL
        """
        # Get the current site
        current_site = get_current_site(request)
        
        # Build the callback URL manually
        protocol = 'https' if request.is_secure() else 'http'
        callback_url = f"{protocol}://{current_site.domain}/accounts/google/login/callback/"
        
        logger.info(f"Generated callback URL: {callback_url}")
        return callback_url


class FixedOAuth2CallbackView(OAuth2CallbackView):
    """
    Custom OAuth2 callback view that prevents the /None redirect issue
    """
    
    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch to catch and fix the redirect
        """
        try:
            # Call the parent dispatch
            response = super().dispatch(request, *args, **kwargs)
            
            # Check if response is None or if it's a redirect to None
            if response is None:
                logger.warning(f"OAuth callback returned None response")
                
                # Check if user is authenticated
                if request.user.is_authenticated:
                    # Check if they need to complete registration
                    try:
                        profile = request.user.profile
                        if not profile.has_completed_registration:
                            logger.info(f"Redirecting new SSO user to post-registration")
                            return redirect('accounts:post_registration')
                    except Exception:
                        # Profile doesn't exist, redirect to post-registration
                        logger.info(f"Profile not found, redirecting to post-registration")
                        return redirect('accounts:post_registration')
                    
                    # User has completed registration, go to home
                    logger.info(f"User has completed registration, redirecting to home")
                    return redirect('core:home')
                else:
                    # Not authenticated, go to login
                    logger.warning(f"User not authenticated after OAuth, redirecting to login")
                    return redirect('account_login')
            
            # Check if it's a redirect response
            if hasattr(response, 'status_code') and response.status_code in [301, 302, 303, 307, 308]:
                # Get the redirect URL
                redirect_url = response.get('Location', '')
                
                logger.info(f"OAuth callback redirect URL: {redirect_url}")
                
                # If it's redirecting to /None or None, fix it
                if not redirect_url or redirect_url == 'None' or '/None' in redirect_url or redirect_url.endswith('/None'):
                    logger.warning(f"Caught invalid redirect URL: {redirect_url}")
                    
                    # Check if user is authenticated
                    if request.user.is_authenticated:
                        # Check if they need to complete registration
                        try:
                            profile = request.user.profile
                            if not profile.has_completed_registration:
                                logger.info(f"Redirecting new SSO user to post-registration")
                                return redirect('accounts:post_registration')
                        except Exception:
                            # Profile doesn't exist, redirect to post-registration
                            logger.info(f"Profile not found, redirecting to post-registration")
                            return redirect('accounts:post_registration')
                        
                        # User has completed registration, go to home
                        logger.info(f"User has completed registration, redirecting to home")
                        return redirect('core:home')
                    else:
                        # Not authenticated, go to login
                        logger.warning(f"User not authenticated after OAuth, redirecting to login")
                        return redirect('account_login')
            
            return response
            
        except Exception as e:
            logger.error(f"Error in OAuth callback: {str(e)}", exc_info=True)
            messages.error(request, "An error occurred during sign-in. Please try again.")
            return redirect('account_login')


oauth2_login = OAuth2LoginView.adapter_view(FixedGoogleOAuth2Adapter)
oauth2_callback = FixedOAuth2CallbackView.adapter_view(FixedGoogleOAuth2Adapter)
