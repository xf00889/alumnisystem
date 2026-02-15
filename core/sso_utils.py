"""
SSO Configuration Utilities
"""
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def get_sso_providers_config():
    """
    Get SSO providers configuration from database.
    Uses caching to avoid database queries on every request.
    Returns configuration in django-allauth format.
    """
    cache_key = 'sso_providers_config'
    cached_config = cache.get(cache_key)
    
    if cached_config is not None:
        return cached_config
    
    try:
        from .models import SSOConfig
        config = SSOConfig.get_active_providers()
        
        # Cache for 5 minutes
        cache.set(cache_key, config, 300)
        return config
    except Exception as e:
        logger.error(f"Error loading SSO configuration from database: {str(e)}")
        # Return empty dict if database not ready or error occurs
        return {}


def clear_sso_cache():
    """
    Clear cached SSO configuration.
    Call this when SSO configuration is updated.
    """
    cache.delete('sso_providers_config')


def get_socialaccount_providers():
    """
    Get SOCIALACCOUNT_PROVIDERS setting with database configuration merged in.
    This function is called by settings.py to dynamically load SSO config.
    """
    # Start with default/fallback configuration from settings
    default_config = {
        'google': {
            'SCOPE': ['profile', 'email'],
            'AUTH_PARAMS': {'access_type': 'online'},
            'VERIFIED_EMAIL': True,
        }
    }
    
    try:
        # Try to load from database
        db_config = get_sso_providers_config()
        
        if db_config:
            # Database configuration takes precedence
            return db_config
        else:
            # No database config, use default
            return default_config
    except Exception as e:
        # If database is not ready (e.g., during migrations), use default
        logger.debug(f"Using default SSO config (database not ready): {str(e)}")
        return default_config


def update_allauth_providers():
    """
    Update django-allauth providers configuration at runtime.
    This is called after SSO configuration changes.
    """
    try:
        from allauth.socialaccount import providers
        
        # Clear cache
        clear_sso_cache()
        
        # Get new configuration
        new_config = get_sso_providers_config()
        
        # Update settings
        settings.SOCIALACCOUNT_PROVIDERS = new_config
        
        # Force allauth to reload provider registry
        if hasattr(providers, 'registry'):
            providers.registry.loaded = False
            providers.registry.load()
        
        logger.info("SSO providers configuration updated successfully")
        return True
    except Exception as e:
        logger.error(f"Error updating allauth providers: {str(e)}")
        return False


def get_enabled_sso_providers():
    """
    Get list of enabled SSO provider names for display on login page.
    Returns: list of provider names (e.g., ['google', 'facebook'])
    """
    try:
        from .models import SSOConfig
        enabled_providers = SSOConfig.objects.filter(
            is_active=True,
            enabled=True
        ).values_list('provider', flat=True)
        
        return list(enabled_providers)
    except Exception as e:
        logger.error(f"Error getting enabled SSO providers: {str(e)}")
        return []


def is_sso_provider_enabled(provider_name):
    """
    Check if a specific SSO provider is enabled.
    
    Args:
        provider_name: Provider name (e.g., 'google', 'facebook')
    
    Returns:
        bool: True if provider is enabled, False otherwise
    """
    try:
        from .models import SSOConfig
        return SSOConfig.objects.filter(
            provider=provider_name,
            is_active=True,
            enabled=True
        ).exists()
    except Exception as e:
        logger.error(f"Error checking SSO provider status: {str(e)}")
        return False


def get_sso_provider_config(provider_name):
    """
    Get configuration for a specific SSO provider.
    
    Args:
        provider_name: Provider name (e.g., 'google', 'facebook')
    
    Returns:
        dict: Provider configuration or None if not found
    """
    try:
        from .models import SSOConfig
        config = SSOConfig.get_provider_config_by_type(provider_name)
        
        if config:
            return config.get_provider_config()
        return None
    except Exception as e:
        logger.error(f"Error getting SSO provider config: {str(e)}")
        return None
