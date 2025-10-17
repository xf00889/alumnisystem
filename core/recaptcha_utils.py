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
    Returns empty string if no active configuration found.
    """
    config = get_recaptcha_config()
    return config.site_key if config else ''


def get_recaptcha_private_key():
    """
    Get the reCAPTCHA private key from database configuration.
    Returns empty string if no active configuration found.
    """
    config = get_recaptcha_config()
    return config.secret_key if config else ''


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
    """
    config = get_recaptcha_config()
    return bool(config and config.enabled and config.site_key and config.secret_key)


def clear_recaptcha_cache():
    """
    Clear the reCAPTCHA configuration cache.
    Call this when reCAPTCHA configuration is updated.
    """
    cache.delete('recaptcha_active_config')
