"""
Email Provider Configuration Model
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

class EmailProvider(models.Model):
    """
    Model to manage email provider selection and configuration
    """
    PROVIDER_CHOICES = [
        ('smtp', 'SMTP'),
        ('brevo', 'Brevo API'),
    ]
    
    provider_type = models.CharField(
        max_length=10,
        choices=PROVIDER_CHOICES,
        default='smtp',
        help_text="Email provider to use for sending emails"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Use this provider for sending emails"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    # Usage statistics
    emails_sent = models.PositiveIntegerField(
        default=0,
        help_text="Number of emails sent using this provider"
    )
    last_error = models.TextField(
        blank=True,
        help_text="Last error message (if any)"
    )
    
    class Meta:
        verbose_name = "Email Provider"
        verbose_name_plural = "Email Providers"
        ordering = ['-is_active', '-created_at']
    
    def __str__(self):
        status = "✓" if self.is_active else "✗"
        return f"{status} {self.get_provider_type_display()}"
    
    def clean(self):
        """Validate email provider configuration"""
        super().clean()
        
        # Ensure only one active provider
        if self.is_active:
            active_providers = EmailProvider.objects.filter(is_active=True).exclude(pk=self.pk)
            if active_providers.exists():
                raise ValidationError({
                    'is_active': 'Only one email provider can be active at a time'
                })
    
    def save(self, *args, **kwargs):
        """Override save to ensure only one active provider"""
        if self.is_active:
            # Deactivate other providers
            EmailProvider.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        
        super().save(*args, **kwargs)
    
    def get_provider_config(self):
        """
        Get the active configuration for this provider
        """
        if self.provider_type == 'smtp':
            from .smtp_config import SMTPConfig
            return SMTPConfig.objects.filter(is_active=True, is_verified=True).first()
        elif self.provider_type == 'brevo':
            from .brevo_config import BrevoConfig
            return BrevoConfig.objects.filter(is_active=True, is_verified=True).first()
        return None
    
    def is_configured(self):
        """
        Check if the provider has a valid configuration
        """
        config = self.get_provider_config()
        return config is not None and config.is_verified
    
    def increment_usage(self):
        """
        Increment the email sent counter
        """
        self.emails_sent += 1
        self.last_used = timezone.now()
        self.save(update_fields=['emails_sent', 'last_used'])
    
    def record_error(self, error_message):
        """
        Record an error message
        """
        self.last_error = error_message
        self.save(update_fields=['last_error'])
    
    @classmethod
    def get_active_provider(cls):
        """
        Get the currently active email provider
        """
        return cls.objects.filter(is_active=True).first()
    
    @classmethod
    def get_available_providers(cls):
        """
        Get all available providers with their configuration status
        """
        providers = []
        for provider_type, display_name in cls.PROVIDER_CHOICES:
            provider_obj = cls.objects.filter(provider_type=provider_type).first()
            if not provider_obj:
                provider_obj = cls(provider_type=provider_type, is_active=False)
            
            providers.append({
                'provider_type': provider_type,
                'display_name': display_name,
                'is_active': provider_obj.is_active,
                'is_configured': provider_obj.is_configured(),
                'emails_sent': provider_obj.emails_sent,
                'last_used': provider_obj.last_used,
                'last_error': provider_obj.last_error,
            })
        
        return providers
