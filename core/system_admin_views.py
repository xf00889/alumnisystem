"""
System settings admin views.
"""
from django.contrib import messages
from django.conf import settings
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from core.decorators import system_config_required
from core.models import SystemSettings
from core.system_settings_utils import (
    DEFAULT_MAINTENANCE_MESSAGE,
    clear_system_settings_cache,
    is_runtime_debug_enabled,
)


@system_config_required
@require_http_methods(["GET", "POST"])
def system_settings_view(request):
    """View and update singleton system settings."""
    settings_obj = SystemSettings.objects.order_by("id").first()
    if settings_obj is None:
        settings_obj = SystemSettings(
            maintenance_mode=False,
            maintenance_message=DEFAULT_MAINTENANCE_MESSAGE,
            runtime_debug=settings.DEBUG,
            updated_by=request.user,
        )
        settings_obj.save()

    if request.method == "POST":
        settings_obj.maintenance_mode = request.POST.get("maintenance_mode") == "on"
        settings_obj.runtime_debug = request.POST.get("runtime_debug") == "on"
        settings_obj.maintenance_message = (
            request.POST.get("maintenance_message", "").strip() or DEFAULT_MAINTENANCE_MESSAGE
        )
        settings_obj.updated_by = request.user
        settings_obj.save()
        clear_system_settings_cache()
        messages.success(request, "System settings updated successfully.")
        return redirect("core:system_settings")

    context = {
        "page_title": "System Controls",
        "settings_obj": settings_obj,
        "env_debug": settings.DEBUG,
        "effective_runtime_debug": is_runtime_debug_enabled(),
    }
    return render(request, "admin/system_settings.html", context)
