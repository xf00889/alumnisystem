"""
Test email sending in production mode (DEBUG=False)
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from core.smtp_settings import update_django_email_settings
from donations.email_utils import send_donation_confirmation_email
from donations.models import Donation
import os

class Command(BaseCommand):
    help = 'Test email sending in production mode'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help='Email address to send test email to'
        )

    def handle(self, *args, **options):
        email = options['email']
        
        # Temporarily set DEBUG=False to simulate production
        original_debug = settings.DEBUG
        settings.DEBUG = False
        
        try:
            self.stdout.write(self.style.SUCCESS('=== Testing Production Mode ==='))
            self.stdout.write(f"DEBUG Mode: {settings.DEBUG}")
            
            # Update email settings
            update_django_email_settings()
            
            self.stdout.write(f"Email Backend: {settings.EMAIL_BACKEND}")
            self.stdout.write(f"Email Host: {settings.EMAIL_HOST}")
            self.stdout.write(f"Email User: {settings.EMAIL_HOST_USER}")
            self.stdout.write(f"From Email: {settings.DEFAULT_FROM_EMAIL}")
            
            # Create a test donation
            from donations.models import Campaign
            from django.utils import timezone
            
            campaign = Campaign.objects.first()
            if not campaign:
                self.stdout.write(self.style.ERROR('No campaigns found. Please create a campaign first.'))
                return
            
            donation = Donation.objects.create(
                campaign=campaign,
                amount=100.00,
                donor_name='Production Test Donor',
                donor_email=email,
                message='Testing email in production mode',
                status='pending_payment',
                donation_date=timezone.now()
            )
            
            self.stdout.write(f'Created test donation: {donation.pk}')
            
            # Send confirmation email
            result = send_donation_confirmation_email(donation)
            
            if result:
                self.stdout.write(self.style.SUCCESS(f'✅ Email sent successfully to {email}'))
                self.stdout.write(self.style.SUCCESS('Check your email inbox for the confirmation!'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ Failed to send email to {email}'))
            
            # Clean up test donation
            donation.delete()
            self.stdout.write('Test donation cleaned up.')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
        finally:
            # Restore original DEBUG setting
            settings.DEBUG = original_debug
