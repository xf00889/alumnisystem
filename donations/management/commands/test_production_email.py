"""
Management command to test email sending on production
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from core.email_utils import send_email_with_smtp_config, get_current_smtp_info
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test email sending on production'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help='Email address to send test email to'
        )
        parser.add_argument(
            '--check-config',
            action='store_true',
            help='Only check email configuration without sending'
        )

    def handle(self, *args, **options):
        email = options['email']
        check_config_only = options['check_config']
        
        # Get current SMTP configuration
        smtp_info = get_current_smtp_info()
        
        self.stdout.write(self.style.SUCCESS('=== Email Configuration Check ==='))
        self.stdout.write(f"DEBUG Mode: {settings.DEBUG}")
        self.stdout.write(f"Email Backend: {smtp_info.get('backend', 'Unknown')}")
        self.stdout.write(f"SMTP Host: {smtp_info.get('host', 'Not configured')}")
        self.stdout.write(f"SMTP Port: {smtp_info.get('port', 'Not configured')}")
        self.stdout.write(f"SMTP Username: {smtp_info.get('username', 'Not configured')}")
        self.stdout.write(f"From Email: {smtp_info.get('from_email', 'Not configured')}")
        self.stdout.write(f"Use TLS: {smtp_info.get('use_tls', 'Not configured')}")
        self.stdout.write(f"Use SSL: {smtp_info.get('use_ssl', 'Not configured')}")
        
        if 'error' in smtp_info:
            self.stdout.write(self.style.ERROR(f"Configuration Error: {smtp_info['error']}"))
            return
        
        if check_config_only:
            self.stdout.write(self.style.SUCCESS('Configuration check completed'))
            return
        
        # Test email sending
        self.stdout.write(self.style.SUCCESS('\n=== Testing Email Sending ==='))
        
        try:
            result = send_email_with_smtp_config(
                subject='Test Email from NORSU Alumni System',
                message=f'''
Hello!

This is a test email from the NORSU Alumni System to verify that email sending is working correctly on production.

Email Configuration:
- Backend: {smtp_info.get('backend', 'Unknown')}
- Host: {smtp_info.get('host', 'Not configured')}
- Port: {smtp_info.get('port', 'Not configured')}
- Username: {smtp_info.get('username', 'Not configured')}

If you receive this email, the email system is working correctly!

Best regards,
NORSU Alumni System
                ''',
                recipient_list=[email],
                fail_silently=False
            )
            
            if result:
                self.stdout.write(self.style.SUCCESS(f'✅ Test email sent successfully to {email}'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ Failed to send test email to {email}'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error sending test email: {str(e)}'))
            logger.error(f"Email test failed: {str(e)}")
