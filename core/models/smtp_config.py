"""
SMTP Configuration Model
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class SMTPConfig(models.Model):
    """
    Model to store SMTP configuration settings
    """
    name = models.CharField(
        max_length=100,
        help_text="Configuration name (e.g., 'Gmail', 'Outlook', 'Custom')"
    )
    
    # SMTP Server Settings
    host = models.CharField(
        max_length=255,
        help_text="SMTP server host (e.g., smtp.gmail.com)"
    )
    port = models.PositiveIntegerField(
        default=587,
        help_text="SMTP server port (587 for TLS, 465 for SSL, 25 for non-encrypted)"
    )
    use_tls = models.BooleanField(
        default=True,
        help_text="Use TLS encryption (recommended for port 587)"
    )
    use_ssl = models.BooleanField(
        default=False,
        help_text="Use SSL encryption (for port 465)"
    )
    
    # Authentication
    username = models.EmailField(
        help_text="SMTP username (usually your email address)"
    )
    password = models.CharField(
        max_length=255,
        help_text="SMTP password or app password"
    )
    
    # Email Settings
    from_email = models.EmailField(
        help_text="Default 'from' email address"
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
        verbose_name = "SMTP Configuration"
        verbose_name_plural = "SMTP Configurations"
        ordering = ['-is_active', '-created_at']
    
    def __str__(self):
        status = "✓" if self.is_verified else "✗"
        return f"{status} {self.name} ({self.host})"
    
    def clean(self):
        """Validate SMTP configuration"""
        super().clean()
        
        # Validate port
        if self.port not in [25, 465, 587, 2525]:
            raise ValidationError({
                'port': 'Port must be 25, 465, 587, or 2525'
            })
        
        # Validate TLS/SSL combination
        if self.use_ssl and self.use_tls:
            raise ValidationError({
                'use_ssl': 'Cannot use both SSL and TLS. Use SSL for port 465, TLS for port 587'
            })
        
        # Validate port and encryption combination
        if self.port == 465 and not self.use_ssl:
            raise ValidationError({
                'use_ssl': 'Port 465 requires SSL encryption'
            })
        
        if self.port == 587 and not self.use_tls:
            raise ValidationError({
                'use_tls': 'Port 587 requires TLS encryption'
            })
    
    def test_connection(self, recipient_email=None):
        """
        Test SMTP connection and authentication
        """
        if recipient_email is None:
            recipient_email = self.username
        try:
            # Create SMTP connection
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.host, self.port)
            else:
                server = smtplib.SMTP(self.host, self.port)
                if self.use_tls:
                    server.starttls()
            
            # Authenticate
            server.login(self.username, self.password)
            
            # Test sending a simple email
            msg = MIMEMultipart()
            msg['From'] = f"{self.from_name} <{self.from_email}>" if self.from_name else self.from_email
            msg['To'] = recipient_email  # Send test email to specified recipient
            msg['Subject'] = "NORSU Alumni - SMTP Configuration Test"
            
            body = f"""
This is a test email to verify your SMTP configuration.

Configuration Details:
- Host: {self.host}
- Port: {self.port}
- TLS: {self.use_tls}
- SSL: {self.use_ssl}
- Username: {self.username}

If you receive this email, your SMTP configuration is working correctly!

Best regards,
NORSU Alumni System
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send test email
            server.send_message(msg)
            server.quit()
            
            # Update test results using update() to avoid datetime field issues
            SMTPConfig.objects.filter(pk=self.pk).update(
                is_verified=True,
                test_result="Connection successful. Test email sent.",
                last_tested=timezone.now()
            )
            
            return True, "SMTP configuration test successful! Test email sent."
            
        except smtplib.SMTPAuthenticationError as e:
            SMTPConfig.objects.filter(pk=self.pk).update(
                is_verified=False,
                test_result=f"Authentication failed: {str(e)}",
                last_tested=timezone.now()
            )
            return False, f"Authentication failed: {str(e)}"
            
        except smtplib.SMTPConnectError as e:
            SMTPConfig.objects.filter(pk=self.pk).update(
                is_verified=False,
                test_result=f"Connection failed: {str(e)}",
                last_tested=timezone.now()
            )
            return False, f"Connection failed: {str(e)}"
            
        except Exception as e:
            SMTPConfig.objects.filter(pk=self.pk).update(
                is_verified=False,
                test_result=f"Test failed: {str(e)}",
                last_tested=timezone.now()
            )
            return False, f"Test failed: {str(e)}"
    
    def get_connection_params(self):
        """
        Get connection parameters for Django email backend
        """
        return {
            'host': self.host,
            'port': self.port,
            'use_tls': self.use_tls,
            'use_ssl': self.use_ssl,
            'username': self.username,
            'password': self.password,
            'from_email': self.from_email,
        }
    
    def save(self, *args, **kwargs):
        """Override save to ensure only one active configuration"""
        if self.is_active:
            # Deactivate other configurations
            SMTPConfig.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        
        super().save(*args, **kwargs)
