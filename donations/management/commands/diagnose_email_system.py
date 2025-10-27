"""
Diagnostic command to check email system status
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from core.smtp_settings import get_smtp_settings, test_smtp_connection
from core.models import SMTPConfig
from donations.models import Donation
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Diagnose email system status'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Email System Diagnostic ==='))
        
        # Check Django settings
        self.stdout.write('\n📧 Django Email Settings:')
        self.stdout.write(f'  DEBUG Mode: {settings.DEBUG}')
        self.stdout.write(f'  Email Backend: {settings.EMAIL_BACKEND}')
        self.stdout.write(f'  Email Host: {settings.EMAIL_HOST}')
        self.stdout.write(f'  Email Port: {settings.EMAIL_PORT}')
        self.stdout.write(f'  Email User: {settings.EMAIL_HOST_USER}')
        self.stdout.write(f'  From Email: {settings.DEFAULT_FROM_EMAIL}')
        
        # Check database SMTP configuration
        self.stdout.write('\n🗄️ Database SMTP Configuration:')
        try:
            config = SMTPConfig.objects.filter(is_active=True, is_verified=True).first()
            if config:
                self.stdout.write(f'  Active Config: {config.name}')
                self.stdout.write(f'  Host: {config.host}')
                self.stdout.write(f'  Port: {config.port}')
                self.stdout.write(f'  Username: {config.username}')
                self.stdout.write(f'  From Email: {config.from_email}')
                self.stdout.write(f'  Use TLS: {config.use_tls}')
                self.stdout.write(f'  Use SSL: {config.use_ssl}')
            else:
                self.stdout.write('  No active SMTP configuration found')
        except Exception as e:
            self.stdout.write(f'  Error: {str(e)}')
        
        # Check current SMTP settings
        self.stdout.write('\n⚙️ Current SMTP Settings:')
        try:
            smtp_settings = get_smtp_settings()
            for key, value in smtp_settings.items():
                if key == 'password':
                    masked_value = '*' * len(str(value)) if value else 'Not set'
                    self.stdout.write(f'  {key}: {masked_value}')
                else:
                    self.stdout.write(f'  {key}: {value}')
        except Exception as e:
            self.stdout.write(f'  Error: {str(e)}')
        
        # Test SMTP connection
        self.stdout.write('\n🔗 SMTP Connection Test:')
        try:
            success, message = test_smtp_connection()
            if success:
                self.stdout.write(self.style.SUCCESS(f'  ✅ {message}'))
            else:
                self.stdout.write(self.style.ERROR(f'  ❌ {message}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Error: {str(e)}'))
        
        # Check recent donations
        self.stdout.write('\n📊 Recent Donations (Last 24 hours):')
        try:
            recent_time = timezone.now() - timedelta(hours=24)
            recent_donations = Donation.objects.filter(created_at__gte=recent_time).order_by('-created_at')
            
            if recent_donations.exists():
                self.stdout.write(f'  Found {recent_donations.count()} donations in the last 24 hours:')
                for donation in recent_donations[:5]:  # Show last 5
                    donor_info = f"{donation.donor_name} ({donation.donor_email})" if donation.donor_email else donation.donor_name
                    self.stdout.write(f'    - ID {donation.pk}: ₱{donation.amount} by {donor_info} - {donation.status}')
            else:
                self.stdout.write('  No donations found in the last 24 hours')
        except Exception as e:
            self.stdout.write(f'  Error: {str(e)}')
        
        # Check signal status
        self.stdout.write('\n🔔 Signal Status:')
        try:
            from django.db.models.signals import post_save
            from donations.signals import send_donation_emails
            
            # Check if signal is connected
            receivers = post_save._live_receivers(sender=Donation)
            signal_connected = any(receiver[1] == send_donation_emails for receiver in receivers)
            
            if signal_connected:
                self.stdout.write('  ✅ Donation email signal is connected')
            else:
                self.stdout.write('  ❌ Donation email signal is NOT connected')
        except Exception as e:
            self.stdout.write(f'  Error: {str(e)}')
        
        # Recommendations
        self.stdout.write('\n💡 Recommendations:')
        if settings.DEBUG:
            self.stdout.write('  - You are in DEBUG mode - emails will be printed to console')
            self.stdout.write('  - On production (DEBUG=False), emails will be sent via SMTP')
        else:
            self.stdout.write('  - You are in production mode - emails should be sent via SMTP')
        
        if not config:
            self.stdout.write('  - No database SMTP config found - using Django settings')
        
        self.stdout.write('\n✅ Diagnostic complete!')
