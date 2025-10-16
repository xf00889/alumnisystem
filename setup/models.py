from django.db import models
from django.utils import timezone


class SiteConfiguration(models.Model):
    """
    Model to store dynamic site configuration settings.
    """
    key = models.CharField(max_length=100, unique=True, help_text="Configuration key")
    value = models.TextField(help_text="Configuration value")
    description = models.TextField(blank=True, help_text="Description of this setting")
    is_active = models.BooleanField(default=True, help_text="Whether this setting is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site Configuration"
        verbose_name_plural = "Site Configurations"

    def __str__(self):
        return f"{self.key}: {self.value[:50]}"

    @classmethod
    def get_setting(cls, key, default=None):
        """Get a configuration setting value."""
        try:
            setting = cls.objects.get(key=key, is_active=True)
            return setting.value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_setting(cls, key, value, description=""):
        """Set a configuration setting value."""
        setting, created = cls.objects.get_or_create(
            key=key,
            defaults={'value': value, 'description': description}
        )
        if not created:
            setting.value = value
            setting.description = description
            setting.save()
        return setting


class EmailConfiguration(models.Model):
    """
    Model to store email configuration settings.
    """
    name = models.CharField(max_length=100, help_text="Configuration name")
    backend = models.CharField(max_length=50, default='console', help_text="Email backend")
    host = models.CharField(max_length=255, blank=True, help_text="SMTP host")
    port = models.IntegerField(default=587, help_text="SMTP port")
    use_tls = models.BooleanField(default=True, help_text="Use TLS")
    username = models.EmailField(blank=True, help_text="SMTP username")
    password = models.CharField(max_length=255, blank=True, help_text="SMTP password")
    from_email = models.EmailField(blank=True, help_text="Default from email")
    is_active = models.BooleanField(default=True, help_text="Whether this configuration is active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Email Configuration"
        verbose_name_plural = "Email Configurations"

    def __str__(self):
        return f"{self.name} ({self.backend})"


class FeatureToggle(models.Model):
    """
    Model to manage feature toggles/flags.
    """
    name = models.CharField(max_length=100, unique=True, help_text="Feature name")
    is_enabled = models.BooleanField(default=False, help_text="Whether the feature is enabled")
    description = models.TextField(blank=True, help_text="Feature description")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Feature Toggle"
        verbose_name_plural = "Feature Toggles"

    def __str__(self):
        return f"{self.name}: {'Enabled' if self.is_enabled else 'Disabled'}"

    @classmethod
    def is_feature_enabled(cls, feature_name):
        """Check if a feature is enabled."""
        try:
            feature = cls.objects.get(name=feature_name)
            return feature.is_enabled
        except cls.DoesNotExist:
            return False


class SetupState(models.Model):
    """
    Model to track the setup completion status of the application.
    """
    is_complete = models.BooleanField(
        default=False,
        help_text="Whether the initial setup has been completed"
    )
    completed_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When the setup was completed"
    )
    setup_data = models.JSONField(
        default=dict, 
        blank=True,
        help_text="Store setup configuration data"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Setup State"
        verbose_name_plural = "Setup States"

    def __str__(self):
        return f"Setup {'Complete' if self.is_complete else 'Incomplete'}"

    def mark_complete(self, setup_data=None):
        """Mark setup as complete with optional data."""
        self.is_complete = True
        self.completed_at = timezone.now()
        if setup_data:
            self.setup_data = setup_data
        self.save()

    @classmethod
    def get_setup_state(cls):
        """Get or create the setup state instance."""
        setup_state, created = cls.objects.get_or_create(
            defaults={'is_complete': False}
        )
        return setup_state

    @classmethod
    def is_setup_complete(cls):
        """Check if setup is complete."""
        try:
            setup_state = cls.objects.first()
            return setup_state.is_complete if setup_state else False
        except Exception:
            return False
