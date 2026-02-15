"""
SSO (Single Sign-On) Configuration Model
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class SSOConfig(models.Model):
    """
    Model to store SSO provider configuration settings
    """
    PROVIDER_CHOICES = [
        ('google', 'Google OAuth'),
    ]
    
    name = models.CharField(
        max_length=100,
        help_text="A descriptive name for this SSO configuration (e.g., 'Google Production')"
    )
    
    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        help_text="SSO provider type"
    )
    
    # OAuth Credentials
    client_id = models.CharField(
        max_length=500,
        help_text="OAuth Client ID from provider console"
    )
    
    secret_key = models.CharField(
        max_length=500,
        help_text="OAuth Client Secret from provider console"
    )
    
    # Provider-specific settings
    scopes = models.TextField(
        default='profile,email',
        help_text="Comma-separated list of OAuth scopes (e.g., 'profile,email')"
    )
    
    verified_email = models.BooleanField(
        default=True,
        help_text="Trust email verification from this provider"
    )
    
    # Configuration Status
    is_active = models.BooleanField(
        default=False,
        help_text="Use this configuration for authentication"
    )
    
    enabled = models.BooleanField(
        default=True,
        help_text="Enable/disable this SSO provider"
    )
    
    is_verified = models.BooleanField(
        default=False,
        help_text="Configuration has been tested and verified"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_tested = models.DateTimeField(null=True, blank=True)
    
    # Test Results
    test_result = models.TextField(
        blank=True,
        help_text="Result of the last configuration test"
    )
    
    # Usage Statistics
    login_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of successful logins using this configuration"
    )
    last_used = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "SSO Configuration"
        verbose_name_plural = "SSO Configurations"
        ordering = ['-is_active', 'provider', '-created_at']
        unique_together = [['provider', 'is_active']]  # Only one active config per provider
    
    def __str__(self):
        status = "✓" if self.is_verified else "✗"
        enabled = "ON" if self.enabled else "OFF"
        return f"{status} {self.name} ({self.get_provider_display()}) - {enabled}"
    
    def clean(self):
        """Validate SSO configuration"""
        super().clean()
        
        # Validate client ID and secret
        if not self.client_id or len(self.client_id) < 10:
            raise ValidationError({
                'client_id': 'Client ID appears to be invalid or too short'
            })
        
        if not self.secret_key or len(self.secret_key) < 10:
            raise ValidationError({
                'secret_key': 'Secret key appears to be invalid or too short'
            })
        
        # Validate scopes
        if not self.scopes:
            raise ValidationError({
                'scopes': 'At least one scope is required'
            })
        
        # Ensure only one active config per provider
        if self.is_active:
            existing = SSOConfig.objects.filter(
                provider=self.provider,
                is_active=True
            ).exclude(pk=self.pk)
            
            if existing.exists():
                raise ValidationError({
                    'is_active': f'Another {self.get_provider_display()} configuration is already active'
                })
    
    def get_scopes_list(self):
        """Get scopes as a list"""
        return [s.strip() for s in self.scopes.split(',') if s.strip()]
    
    def get_provider_config(self):
        """
        Get provider configuration in django-allauth format
        """
        config = {
            'APP': {
                'client_id': self.client_id,
                'secret': self.secret_key,
            },
            'SCOPE': self.get_scopes_list(),
            'VERIFIED_EMAIL': self.verified_email,
        }
        
        # Provider-specific settings
        if self.provider == 'google':
            config['AUTH_PARAMS'] = {
                'access_type': 'online',
            }
        elif self.provider == 'facebook':
            config.update({
                'METHOD': 'oauth2',
                'AUTH_PARAMS': {'auth_type': 'reauthenticate'},
                'INIT_PARAMS': {'cookie': True},
                'FIELDS': [
                    'id', 'email', 'name', 'first_name', 'last_name',
                    'verified', 'locale', 'timezone', 'link', 'gender',
                    'updated_time',
                ],
                'EXCHANGE_TOKEN': True,
                'VERSION': 'v13.0',
            })
        
        return config
    
    def test_configuration(self):
        """
        Test the SSO configuration
        Note: Full OAuth testing requires actual authentication flow,
        so this performs basic validation checks
        """
        try:
            # Validate required fields
            if not self.client_id or not self.secret_key:
                return False, "Client ID and Secret Key are required"
            
            if len(self.client_id) < 10:
                return False, "Client ID appears to be invalid"
            
            if len(self.secret_key) < 10:
                return False, "Secret Key appears to be invalid"
            
            if not self.get_scopes_list():
                return False, "At least one scope is required"
            
            # Update test results
            SSOConfig.objects.filter(pk=self.pk).update(
                is_verified=True,
                test_result="Configuration validation successful. Full OAuth flow testing requires actual login attempt.",
                last_tested=timezone.now()
            )
            
            return True, "SSO configuration validation successful. Test by attempting to login with this provider."
            
        except Exception as e:
            error_msg = f"Configuration test failed: {str(e)}"
            SSOConfig.objects.filter(pk=self.pk).update(
                is_verified=False,
                test_result=error_msg,
                last_tested=timezone.now()
            )
            return False, error_msg
    
    def increment_usage(self):
        """
        Increment the login counter
        """
        self.login_count += 1
        self.last_used = timezone.now()
        self.save(update_fields=['login_count', 'last_used'])
    
    def save(self, *args, **kwargs):
        """Override save to ensure only one active configuration per provider"""
        if self.is_active:
            # Deactivate other configurations for the same provider
            SSOConfig.objects.filter(
                provider=self.provider,
                is_active=True
            ).exclude(pk=self.pk).update(is_active=False)
        
        super().save(*args, **kwargs)
    
    @classmethod
    def get_active_providers(cls):
        """
        Get all active SSO providers as a dictionary for django-allauth
        """
        providers = {}
        active_configs = cls.objects.filter(is_active=True, enabled=True)
        
        for config in active_configs:
            providers[config.provider] = config.get_provider_config()
        
        return providers
    
    @classmethod
    def get_provider_config_by_type(cls, provider_type):
        """
        Get active configuration for a specific provider
        """
        return cls.objects.filter(
            provider=provider_type,
            is_active=True,
            enabled=True
        ).first()
