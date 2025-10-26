"""
Management command to test donation email functionality
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from donations.models import Campaign, CampaignType, Donation
from donations.email_utils import send_donation_confirmation_email, send_donation_status_update_email, send_donation_receipt_email
from django.utils import timezone
from decimal import Decimal

User = get_user_model()

class Command(BaseCommand):
    help = 'Test donation email functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send test emails to',
            required=True
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['confirmation', 'status', 'receipt'],
            default='confirmation',
            help='Type of email to test'
        )

    def handle(self, *args, **options):
        email = options['email']
        email_type = options['type']
        
        self.stdout.write(f"Testing {email_type} email to {email}")
        
        # Create test campaign type if it doesn't exist
        campaign_type, created = CampaignType.objects.get_or_create(
            name="Test Campaign Type",
            defaults={'description': "Test campaign type for email testing"}
        )
        
        # Create test campaign
        campaign, created = Campaign.objects.get_or_create(
            name="Test Email Campaign",
            defaults={
                'campaign_type': campaign_type,
                'description': 'This is a test campaign for email functionality testing.',
                'short_description': 'Test campaign for emails',
                'goal_amount': Decimal('10000.00'),
                'current_amount': Decimal('0.00'),
                'status': 'active',
                'visibility': 'public'
            }
        )
        
        # Create test donation
        donation = Donation.objects.create(
            campaign=campaign,
            donor_name="Test Donor",
            donor_email=email,
            amount=Decimal('100.00'),
            donation_date=timezone.now(),
            status='pending_verification',
            payment_method='gcash',
            is_anonymous=False,
            message="This is a test donation for email functionality testing.",
            reference_number="TEST-2024-001"
        )
        
        try:
            if email_type == 'confirmation':
                success = send_donation_confirmation_email(donation)
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(f"✅ Confirmation email sent successfully to {email}")
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f"❌ Failed to send confirmation email to {email}")
                    )
                    
            elif email_type == 'status':
                # Update donation status to test status email
                donation.status = 'completed'
                donation.verification_date = timezone.now()
                donation.save()
                
                success = send_donation_status_update_email(donation, 'pending_verification')
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(f"✅ Status update email sent successfully to {email}")
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f"❌ Failed to send status update email to {email}")
                    )
                    
            elif email_type == 'receipt':
                # Set donation as completed for receipt
                donation.status = 'completed'
                donation.verification_date = timezone.now()
                donation.save()
                
                success = send_donation_receipt_email(donation)
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(f"✅ Receipt email sent successfully to {email}")
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f"❌ Failed to send receipt email to {email}")
                    )
            
            # Clean up test data
            donation.delete()
            if created:
                campaign.delete()
                campaign_type.delete()
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error testing {email_type} email: {str(e)}")
            )
            # Clean up on error
            donation.delete()
            if created:
                campaign.delete()
                campaign_type.delete()
