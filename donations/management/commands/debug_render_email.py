"""
Management command to debug email configuration on Render
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from core.smtp_settings import get_smtp_settings, update_django_email_settings
from core.models import SMTPConfig
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Debug email configuration for Render deployment'

    def handle(self, *args, **options):
        self.stdout.write("=== Render Email Configuration Debug ===\n")
        
        # 1. Check Django settings
        self.stdout.write("📧 Django Settings:")
        self.stdout.write(f"  DEBUG: {settings.DEBUG}")
        self.stdout.write(f"  EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"  EMAIL_HOST: {settings.EMAIL_HOST}")
        self.stdout.write(f"  EMAIL_PORT: {settings.EMAIL_PORT}")
        self.stdout.write(f"  EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        self.stdout.write(f"  DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write()
        
        # 2. Check database SMTP configuration
        self.stdout.write("🗄️ Database SMTP Configuration:")
        try:
            active_config = SMTPConfig.objects.filter(is_active=True, is_verified=True).first()
            if active_config:
                self.stdout.write(f"  Active Config: {active_config.name}")
                self.stdout.write(f"  Host: {active_config.host}")
                self.stdout.write(f"  Port: {active_config.port}")
                self.stdout.write(f"  Username: {active_config.username}")
                self.stdout.write(f"  From Email: {active_config.from_email}")
                self.stdout.write(f"  Use TLS: {active_config.use_tls}")
                self.stdout.write(f"  Use SSL: {active_config.use_ssl}")
                self.stdout.write(f"  Is Verified: {active_config.is_verified}")
            else:
                self.stdout.write("  No active SMTP configuration found")
        except Exception as e:
            self.stdout.write(f"  Error: {str(e)}")
        self.stdout.write()
        
        # 3. Check current SMTP settings (from cache/database)
        self.stdout.write("⚙️ Current SMTP Settings (from get_smtp_settings):")
        try:
            smtp_settings = get_smtp_settings()
            for key, value in smtp_settings.items():
                if key == 'password':
                    self.stdout.write(f"  {key}: {'*' * len(str(value)) if value else 'None'}")
                else:
                    self.stdout.write(f"  {key}: {value}")
        except Exception as e:
            self.stdout.write(f"  Error: {str(e)}")
        self.stdout.write()
        
        # 4. Test update_django_email_settings
        self.stdout.write("🔄 Testing update_django_email_settings():")
        try:
            # Store original settings
            original_backend = settings.EMAIL_BACKEND
            original_host = settings.EMAIL_HOST
            
            # Call update function
            update_django_email_settings()
            
            # Check if settings changed
            self.stdout.write(f"  Original EMAIL_BACKEND: {original_backend}")
            self.stdout.write(f"  New EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
            self.stdout.write(f"  Original EMAIL_HOST: {original_host}")
            self.stdout.write(f"  New EMAIL_HOST: {settings.EMAIL_HOST}")
            
            if settings.EMAIL_BACKEND != original_backend:
                self.stdout.write("  ✅ EMAIL_BACKEND was updated")
            else:
                self.stdout.write("  ⚠️ EMAIL_BACKEND was NOT updated")
                
        except Exception as e:
            self.stdout.write(f"  Error: {str(e)}")
        self.stdout.write()
        
        # 5. Final configuration check
        self.stdout.write("🎯 Final Configuration:")
        self.stdout.write(f"  EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"  EMAIL_HOST: {settings.EMAIL_HOST}")
        self.stdout.write(f"  EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        self.stdout.write(f"  DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        
        # 6. Test email sending
        self.stdout.write("\n📧 Testing Email Sending:")
        try:
            from django.core.mail import send_mail
            result = send_mail(
                'Render Email Test',
                'This is a test email from Render deployment.',
                settings.DEFAULT_FROM_EMAIL,
                ['hutchiejn@gmail.com'],
                fail_silently=False,
            )
            self.stdout.write(f"  ✅ Email sent successfully: {result}")
        except Exception as e:
            self.stdout.write(f"  ❌ Email sending failed: {str(e)}")
        
        self.stdout.write("\n✅ Debug complete!")
