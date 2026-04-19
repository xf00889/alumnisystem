"""
Helpers for reading runtime system settings with caching.
"""
from django.conf import settings
from django.core.cache import cache


CACHE_KEY = "core_system_settings_cache"
CACHE_TTL = 300
DEFAULT_MAINTENANCE_MESSAGE = "The site is under maintenance. Please try again later."


def _default_data():
    return {
        "maintenance_mode": False,
        "maintenance_message": DEFAULT_MAINTENANCE_MESSAGE,
        "runtime_debug": settings.DEBUG,
    }


def clear_system_settings_cache():
    """Clear cached system settings."""
    cache.delete(CACHE_KEY)


def get_system_settings():
    """
    Return system settings as a simple dict.
    Falls back safely when database tables are not ready.
    """
    cached = cache.get(CACHE_KEY)
    if cached is not None:
        return cached

    data = _default_data()
    try:
        from core.models import SystemSettings

        config = SystemSettings.objects.order_by("id").first()
        if config:
            data = {
                "maintenance_mode": bool(config.maintenance_mode),
                "maintenance_message": config.maintenance_message or DEFAULT_MAINTENANCE_MESSAGE,
                "runtime_debug": bool(config.runtime_debug),
            }
    except Exception:
        # Database may be unavailable during startup/migrations.
        data = _default_data()

    cache.set(CACHE_KEY, data, CACHE_TTL)
    return data


def is_maintenance_mode_enabled():
    return bool(get_system_settings().get("maintenance_mode", False))


def get_maintenance_message():
    return get_system_settings().get("maintenance_message", DEFAULT_MAINTENANCE_MESSAGE)


def is_runtime_debug_enabled():
    return bool(get_system_settings().get("runtime_debug", settings.DEBUG))
