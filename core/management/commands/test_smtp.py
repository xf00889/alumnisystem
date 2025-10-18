"""
Management command to test SMTP configuration
"""
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from core.email_utils import send_email_with_smtp_config, get_current_smtp_info
from core.smtp_settings import get_smtp_settings, test_smtp_connection
from core.models import SMTPConfig


class Command(BaseCommand):
    help = 'Test SMTP configuration and send a test email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send test email to',
            default=None
        )
        parser.add_argument(
            '--info-only',
            action='store_true',
            help='Only show SMTP configuration info without sending email',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== SMTP Configuration Test ===\n'))
        
        # Show current SMTP info
        smtp_info = get_current_smtp_info()
        self.stdout.write('Current SMTP Configuration:')
        for key, value in smtp_info.items():
            self.stdout.write(f'  {key}: {value}')
        
        # Show database configurations
        self.stdout.write('\nDatabase SMTP Configurations:')
        configs = SMTPConfig.objects.all()
        if configs.exists():
            for config in configs:
                status = "✓ Active & Verified" if config.is_active and config.is_verified else "✗ Inactive/Unverified"
                self.stdout.write(f'  {config.name}: {config.host}:{config.port} - {status}')
        else:
            self.stdout.write('  No SMTP configurations found in database')
        
        # Test connection
        self.stdout.write('\nTesting SMTP Connection:')
        try:
            success, message = test_smtp_connection()
            if success:
                self.stdout.write(self.style.SUCCESS(f'✓ {message}'))
            else:
                self.stdout.write(self.style.ERROR(f'✗ {message}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Connection test failed: {str(e)}'))
        
        # Send test email if requested
        if not options['info_only']:
            test_email = options['email']
            if not test_email:
                # Try to get email from active config
                active_config = SMTPConfig.objects.filter(is_active=True, is_verified=True).first()
                if active_config:
                    test_email = active_config.username
                else:
                    self.stdout.write(self.style.WARNING('\nNo email address provided and no active SMTP config found.'))
                    self.stdout.write('Use --email <address> to specify a test email address.')
                    return
            
            self.stdout.write(f'\nSending test email to: {test_email}')
            try:
                result = send_email_with_smtp_config(
                    subject='NORSU Alumni - SMTP Test Email',
                    message='''
This is a test email from the NORSU Alumni System.

If you receive this email, your SMTP configuration is working correctly!

Best regards,
NORSU Alumni System
                    ''',
                    recipient_list=[test_email],
                    fail_silently=False
                )
                
                if result:
                    self.stdout.write(self.style.SUCCESS('✓ Test email sent successfully!'))
                else:
                    self.stdout.write(self.style.ERROR('✗ Failed to send test email'))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Error sending test email: {str(e)}'))
        
        self.stdout.write('\n=== Test Complete ===')
