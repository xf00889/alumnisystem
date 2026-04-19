"""
System settings model for runtime operational controls.
"""
from django.conf import settings
from django.db import models


def default_runtime_debug():
    """Mirror the deployment default on first record creation."""
    return settings.DEBUG


class SystemSettings(models.Model):
    """
    Singleton-style settings for maintenance mode and app-level runtime debug.
    """

    maintenance_mode = models.BooleanField(
        default=False,
        help_text="When enabled, public pages are replaced with the maintenance page.",
    )
    maintenance_message = models.TextField(
        default="The site is under maintenance. Please try again later.",
        blank=True,
        help_text="Message shown to visitors when maintenance mode is enabled.",
    )
    runtime_debug = models.BooleanField(
        default=default_runtime_debug,
        help_text="App-level runtime debug flag (does not change Django settings.DEBUG).",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_system_settings",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"

    def __str__(self):
        return "System Settings"

    def save(self, *args, **kwargs):
        """
        Keep a single row by reusing the first row's primary key for new records.
        """
        if not self.pk:
            existing = SystemSettings.objects.order_by("id").first()
            if existing:
                self.pk = existing.pk
        super().save(*args, **kwargs)

        # Clear cache after each update.
        from core.system_settings_utils import clear_system_settings_cache

        clear_system_settings_cache()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        from core.system_settings_utils import clear_system_settings_cache

        clear_system_settings_cache()
