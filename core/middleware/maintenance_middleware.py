"""
Middleware enforcing maintenance mode outside admin control paths.
"""
from django.shortcuts import render

from core.system_settings_utils import get_maintenance_message, is_maintenance_mode_enabled


class MaintenanceModeMiddleware:
    """
    Block non-admin pages when maintenance mode is enabled.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed_prefixes = (
            "/admin-dashboard",
            "/accounts/login/",
            "/accounts/logout/",
            "/accounts/google/login/",
            "/accounts/google/login/callback/",
            "/static/",
            "/media/",
            "/favicon.ico",
        )

    def __call__(self, request):
        if not is_maintenance_mode_enabled():
            return self.get_response(request)

        path = request.path
        if self._is_allowed(path):
            return self.get_response(request)

        response = render(
            request,
            "maintenance.html",
            {"maintenance_message": get_maintenance_message()},
            status=503,
        )
        response["Retry-After"] = "3600"
        return response

    def _is_allowed(self, path):
        if path.startswith("/admin/"):
            return False
        return any(path.startswith(prefix) for prefix in self.allowed_prefixes)
