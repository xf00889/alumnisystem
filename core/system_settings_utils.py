"""Helpers for reading runtime system settings with caching.

Runtime settings are consulted by middleware on *every* request. A temporary
cache outage must not turn public pages and static redirects into HTTP 500s.
The database remains authoritative whenever the cache cannot be reached.
"""
import logging

from django.conf import settings
from django.core.cache import cache


logger = logging.getLogger(__name__)
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
    """Invalidate stored settings without failing administrative updates on cache outages."""
    try:
        cache.delete(CACHE_KEY)
    except Exception:
        logger.warning('System settings cache invalidation unavailable; using database settings')


def get_system_settings():
    """Read runtime settings, falling back to DB if Redis/cache is unavailable."""
    cache_available = True
    try:
        cached = cache.get(CACHE_KEY)
        if cached is not None:
            return cached
    except Exception:
        cache_available = False
        # Never include cache URLs or credentials in log messages.
        logger.warning('System settings cache unavailable; reading database settings')

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

    if cache_available:
        try:
            cache.set(CACHE_KEY, data, CACHE_TTL)
        except Exception:
            logger.warning('System settings cache write unavailable; using database settings')
    return data


def is_maintenance_mode_enabled():
    return bool(get_system_settings().get("maintenance_mode", False))


def get_maintenance_message():
    return get_system_settings().get("maintenance_message", DEFAULT_MAINTENANCE_MESSAGE)


def is_runtime_debug_enabled():
    return bool(get_system_settings().get("runtime_debug", settings.DEBUG))
