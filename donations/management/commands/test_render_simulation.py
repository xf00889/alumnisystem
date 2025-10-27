"""
Test Render email system with simulated Render environment
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test Render email system by simulating Render environment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send test email to',
            default='test@example.com'
        )

    def handle(self, *args, **options):
        test_email = options['email']
        
        self.stdout.write("=== RENDER EMAIL SYSTEM TEST ===")
        
        # Simulate Render environment
        original_render = os.getenv('RENDER')
        os.environ['RENDER'] = 'true'
        
        try:
            # Check current email settings
            self.stdout.write(f"\n1. Current Email Settings:")
            self.stdout.write(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
            self.stdout.write(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
            self.stdout.write(f"   EMAIL_PORT: {settings.EMAIL_PORT}")
            self.stdout.write(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
            
            # Update email settings with Render detection
            self.stdout.write(f"\n2. Updating Email Settings for Render...")
            from core.smtp_settings import update_django_email_settings
            update_django_email_settings()
            
            # Check updated settings
            self.stdout.write(f"\n3. Updated Email Settings:")
            self.stdout.write(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
            self.stdout.write(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
            self.stdout.write(f"   EMAIL_PORT: {settings.EMAIL_PORT}")
            self.stdout.write(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
            
            # Test email sending
            self.stdout.write(f"\n4. Testing Email Sending to: {test_email}")
            
            from core.email_utils import send_email_with_smtp_config
            
            try:
                result = send_email_with_smtp_config(
                    subject="Render Email System Test",
                    message="This is a test email using the Render-compatible email system.",
                    recipient_list=[test_email],
                    from_email=settings.DEFAULT_FROM_EMAIL
                )
                
                if result:
                    self.stdout.write("✓ Email sending test completed successfully")
                    self.stdout.write("Note: On Render, emails will be logged to console instead of sent")
                else:
                    self.stdout.write("✗ Email sending test failed")
                    
            except Exception as e:
                self.stdout.write(f"✗ Email sending test failed with error: {str(e)}")
            
            # Test Render detection
            self.stdout.write(f"\n5. Render Detection Test:")
            from core.render_email_fallback import is_render_hosting
            is_render = is_render_hosting()
            self.stdout.write(f"   is_render_hosting(): {is_render}")
            
            # Test SendGrid status
            self.stdout.write(f"\n6. SendGrid Status:")
            from core.sendgrid_email import get_sendgrid_status
            sendgrid_status = get_sendgrid_status()
            self.stdout.write(f"   SendGrid Status: {sendgrid_status}")
            
            if sendgrid_status == "not_configured":
                self.stdout.write("   To enable SendGrid:")
                self.stdout.write("   1. Sign up at sendgrid.com")
                self.stdout.write("   2. Get API key")
                self.stdout.write("   3. Set RENDER environment variable: SENDGRID_API_KEY=your_key")
                self.stdout.write("   4. Add to requirements.txt: sendgrid==6.10.0")
            
        finally:
            # Restore original environment
            if original_render is None:
                os.environ.pop('RENDER', None)
            else:
                os.environ['RENDER'] = original_render
        
        self.stdout.write(f"\n=== END TEST ===")
