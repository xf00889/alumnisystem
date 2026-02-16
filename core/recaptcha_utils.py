"""
reCAPTCHA Utility Functions
"""
from django.core.cache import cache
from .models.recaptcha_config import ReCaptchaConfig


def get_recaptcha_config():
    """
    Get the active reCAPTCHA configuration from database.
    Uses caching to avoid database queries on every request.
    """
    cache_key = 'recaptcha_active_config'
    config = cache.get(cache_key)
    
    if config is None:
        config = ReCaptchaConfig.get_active_config()
        # Cache for 5 minutes
        cache.set(cache_key, config, 300)
    
    return config


def get_recaptcha_public_key():
    """
    Get the reCAPTCHA public key from database configuration.
    Falls back to Django settings if no database configuration found.
    """
    config = get_recaptcha_config()
    if config and config.site_key:
        return config.site_key
    
    # Fallback to Django settings
    from django.conf import settings
    return getattr(settings, 'RECAPTCHA_PUBLIC_KEY', '')


def get_recaptcha_private_key():
    """
    Get the reCAPTCHA private key from database configuration.
    Falls back to Django settings if no database configuration found.
    """
    config = get_recaptcha_config()
    if config and config.secret_key:
        return config.secret_key
    
    # Fallback to Django settings
    from django.conf import settings
    return getattr(settings, 'RECAPTCHA_PRIVATE_KEY', '')


def get_recaptcha_threshold():
    """
    Get the reCAPTCHA threshold from database configuration.
    Returns 0.5 as default if no active configuration found.
    """
    config = get_recaptcha_config()
    return config.threshold if config else 0.5


def get_recaptcha_version():
    """
    Get the reCAPTCHA version from database configuration.
    Returns 'v3' as default if no active configuration found.
    """
    config = get_recaptcha_config()
    return config.version if config else 'v3'


def is_recaptcha_enabled():
    """
    Check if reCAPTCHA is enabled (has active configuration with valid keys and enabled=True).
    Only checks database configuration - does NOT fall back to Django settings.
    """
    config = get_recaptcha_config()
    if config and config.enabled and config.site_key and config.secret_key:
        return True
    
    # Do not fall back to Django settings - require explicit database configuration
    return False


def clear_recaptcha_cache():
    """
    Clear the reCAPTCHA configuration cache.
    Call this when reCAPTCHA configuration is updated.
    """
    cache.delete('recaptcha_active_config')
