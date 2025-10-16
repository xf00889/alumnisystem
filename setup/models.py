from django.db import models
from django.utils import timezone


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
