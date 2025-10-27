"""
Test email functionality on Render
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from core.email_utils import send_email_with_smtp_config
from core.render_email_fallback import is_render_hosting, get_render_email_status
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test email functionality on Render'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send test email to',
            default='test@example.com'
        )

    def handle(self, *args, **options):
        test_email = options['email']
        
        self.stdout.write("=== RENDER EMAIL TEST ===")
        
        # Check environment
        if is_render_hosting():
            self.stdout.write("✓ Running on Render hosting")
        else:
            self.stdout.write("Running locally")
        
        # Check email status
        status = get_render_email_status()
        self.stdout.write(f"Email status: {status}")
        
        # Test email sending
        self.stdout.write(f"\nTesting email sending to: {test_email}")
        
        try:
            result = send_email_with_smtp_config(
                subject="Render Email Test",
                message="This is a test email from Render hosting.",
                recipient_list=[test_email],
                from_email=settings.DEFAULT_FROM_EMAIL
            )
            
            if result:
                self.stdout.write("✓ Email sending test completed successfully")
                if is_render_hosting():
                    self.stdout.write("Note: On Render, emails may be logged instead of sent due to network restrictions")
            else:
                self.stdout.write("✗ Email sending test failed")
                
        except Exception as e:
            self.stdout.write(f"✗ Email sending test failed with error: {str(e)}")
            if is_render_hosting():
                self.stdout.write("This is expected on Render due to network restrictions")
        
        self.stdout.write("\n=== END TEST ===")
