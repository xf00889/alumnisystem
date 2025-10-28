"""
Brevo Configuration Model
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import requests
import logging

logger = logging.getLogger(__name__)

class BrevoConfig(models.Model):
    """
    Model to store Brevo API configuration settings
    """
    name = models.CharField(
        max_length=100,
        help_text="Configuration name (e.g., 'Brevo Production', 'Brevo Sandbox')"
    )
    
    # Brevo API Settings
    api_key = models.CharField(
        max_length=255,
        help_text="Brevo API key from your account settings"
    )
    api_url = models.URLField(
        default="https://api.brevo.com/v3/smtp/email",
        help_text="Brevo API endpoint URL"
    )
    
    # Email Settings
    from_email = models.EmailField(
        help_text="Default 'from' email address (must be verified in Brevo)"
    )
    from_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Default 'from' name (optional)"
    )
    
    # Configuration Status
    is_active = models.BooleanField(
        default=False,
        help_text="Use this configuration for sending emails"
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
        help_text="Result of the last test"
    )
    
    class Meta:
        verbose_name = "Brevo Configuration"
        verbose_name_plural = "Brevo Configurations"
        ordering = ['-is_active', '-created_at']
    
    def __str__(self):
        status = "✓" if self.is_verified else "✗"
        return f"{status} {self.name} ({self.from_email})"
    
    def clean(self):
        """Validate Brevo configuration"""
        super().clean()
        
        # Validate API key format (basic check)
        if not self.api_key or len(self.api_key) < 10:
            raise ValidationError({
                'api_key': 'API key appears to be invalid or too short'
            })
        
        # Validate API URL
        if not self.api_url.startswith('https://'):
            raise ValidationError({
                'api_url': 'API URL must use HTTPS'
            })
    
    def test_connection(self, recipient_email=None, send_test_email=False):
        """
        Test Brevo API connection and authentication
        """
        if recipient_email is None:
            recipient_email = self.from_email
        
        try:
            # Test API connection by making a simple request
            headers = {
                'accept': 'application/json',
                'api-key': self.api_key,
                'content-type': 'application/json'
            }
            
            if send_test_email:
                # Send actual test email
                test_data = {
                    "sender": {
                        "name": self.from_name or "NORSU Alumni System",
                        "email": self.from_email
                    },
                    "to": [
                        {
                            "email": recipient_email,
                            "name": "Test Recipient"
                        }
                    ],
                    "subject": "NORSU Alumni - Brevo Configuration Test",
                    "htmlContent": f"""
                    <html>
                    <body>
                        <h2>Brevo Configuration Test</h2>
                        <p>This is a test email to verify your Brevo configuration.</p>
                        <p><strong>Configuration Details:</strong></p>
                        <ul>
                            <li>API URL: {self.api_url}</li>
                            <li>From Email: {self.from_email}</li>
                            <li>From Name: {self.from_name or 'Not set'}</li>
                        </ul>
                        <p>If you receive this email, your Brevo configuration is working correctly!</p>
                        <p>Best regards,<br>NORSU Alumni System</p>
                    </body>
                    </html>
                    """,
                    "textContent": f"""
                    Brevo Configuration Test
                    
                    This is a test email to verify your Brevo configuration.
                    
                    Configuration Details:
                    - API URL: {self.api_url}
                    - From Email: {self.from_email}
                    - From Name: {self.from_name or 'Not set'}
                    
                    If you receive this email, your Brevo configuration is working correctly!
                    
                    Best regards,
                    NORSU Alumni System
                    """
                }
                
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=test_data,
                    timeout=30
                )
                
                if response.status_code == 201:
                    # Update test results
                    BrevoConfig.objects.filter(pk=self.pk).update(
                        is_verified=True,
                        test_result="Connection successful. Test email sent.",
                        last_tested=timezone.now()
                    )
                    return True, f"Brevo configuration test successful! Test email sent to {recipient_email}."
                else:
                    error_msg = f"API request failed: {response.status_code} - {response.text}"
                    BrevoConfig.objects.filter(pk=self.pk).update(
                        is_verified=False,
                        test_result=error_msg,
                        last_tested=timezone.now()
                    )
                    return False, error_msg
            else:
                # Just test API key validity by making a simple request
                # We'll use the account info endpoint for this
                account_url = "https://api.brevo.com/v3/account"
                response = requests.get(account_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    # Update test results
                    BrevoConfig.objects.filter(pk=self.pk).update(
                        is_verified=True,
                        test_result="API key valid. Connection successful.",
                        last_tested=timezone.now()
                    )
                    return True, "Brevo configuration test successful! API key is valid."
                else:
                    error_msg = f"API key validation failed: {response.status_code} - {response.text}"
                    BrevoConfig.objects.filter(pk=self.pk).update(
                        is_verified=False,
                        test_result=error_msg,
                        last_tested=timezone.now()
                    )
                    return False, error_msg
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Connection failed: {str(e)}"
            BrevoConfig.objects.filter(pk=self.pk).update(
                is_verified=False,
                test_result=error_msg,
                last_tested=timezone.now()
            )
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Test failed: {str(e)}"
            BrevoConfig.objects.filter(pk=self.pk).update(
                is_verified=False,
                test_result=error_msg,
                last_tested=timezone.now()
            )
            return False, error_msg
    
    def get_connection_params(self):
        """
        Get connection parameters for Brevo API
        """
        return {
            'api_key': self.api_key,
            'api_url': self.api_url,
            'from_email': self.from_email,
            'from_name': self.from_name,
        }
    
    def save(self, *args, **kwargs):
        """Override save to ensure only one active configuration"""
        if self.is_active:
            # Deactivate other configurations
            BrevoConfig.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        
        super().save(*args, **kwargs)
