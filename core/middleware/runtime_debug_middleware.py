"""
Middleware that overrides Django's settings.DEBUG at runtime
based on the SystemSettings.runtime_debug database flag.

Must be placed early in MIDDLEWARE (after SecurityMiddleware)
so that Django's debug error pages are suppressed when the flag is off.
"""
from django.conf import settings


class RuntimeDebugMiddleware:
    """
    Dynamically sets settings.DEBUG from the SystemSettings singleton.

    When runtime_debug is False in the database, Django's own debug
    error pages (404 with URL list, 500 traceback) are suppressed and
    your custom error handlers take over instead.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Import here to avoid circular imports at startup
        try:
            from core.system_settings_utils import is_runtime_debug_enabled
            settings.DEBUG = is_runtime_debug_enabled()
        except Exception:
            # If DB is unavailable, leave settings.DEBUG as-is
            pass

        return self.get_response(request)
