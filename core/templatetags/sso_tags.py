"""
Custom template tags for SSO functionality
"""
from django import template
from django.urls import reverse
from django.contrib.sites.models import Site

register = template.Library()


@register.simple_tag(takes_context=True)
def sso_login_url(context, provider):
    """
    Generate SSO login URL with proper site handling.
    This fixes the issue where provider_login_url generates URLs with /None.
    """
    try:
        # Build the login URL using the provider-specific URL name
        # allauth uses pattern: {provider}_login
        login_url = reverse(f'{provider}_login')
        
        # Return the relative URL (no need for absolute URL in template)
        return login_url
    except Exception as e:
        # Fallback to the standard allauth URL pattern
        return f'/accounts/{provider}/login/'


@register.simple_tag
def sso_callback_url(provider):
    """
    Generate SSO callback URL.
    """
    try:
        return reverse(f'{provider}_callback')
    except Exception:
        return f'/accounts/{provider}/login/callback/'
