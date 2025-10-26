#!/usr/bin/env python
"""
Test script for donation email functionality
Run this script to test the donation email system
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from django.core.management import call_command
from django.test import TestCase
from django.contrib.auth import get_user_model
from donations.models import Campaign, CampaignType, Donation
from donations.email_utils import send_donation_confirmation_email, send_donation_status_update_email, send_donation_receipt_email
from django.utils import timezone
from decimal import Decimal

User = get_user_model()

def test_donation_emails():
    """Test all donation email types"""
    print("🧪 Testing Donation Email Functionality")
    print("=" * 50)
    
    # Test email address (change this to your email)
    test_email = "test@example.com"
    
    print(f"📧 Testing emails will be sent to: {test_email}")
    print("⚠️  Make sure to update the email address in this script!")
    print()
    
    # Create test data
    print("📝 Creating test data...")
    
    # Create test campaign type
    campaign_type, created = CampaignType.objects.get_or_create(
        name="Test Campaign Type",
        defaults={'description': "Test campaign type for email testing"}
    )
    
    # Create test campaign
    campaign, created = Campaign.objects.get_or_create(
        name="Test Email Campaign",
        defaults={
            'campaign_type': campaign_type,
            'description': 'This is a test campaign for email functionality testing. It helps us verify that our email system is working correctly.',
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
        donor_email=test_email,
        amount=Decimal('100.00'),
        donation_date=timezone.now(),
        status='pending_verification',
        payment_method='gcash',
        is_anonymous=False,
        message="This is a test donation for email functionality testing. Thank you for your support!",
        reference_number="TEST-2024-001"
    )
    
    print(f"✅ Created test donation: {donation.reference_number}")
    print()
    
    # Test 1: Confirmation Email
    print("📧 Test 1: Sending Donation Confirmation Email")
    try:
        success = send_donation_confirmation_email(donation)
        if success:
            print("✅ Confirmation email sent successfully!")
        else:
            print("❌ Failed to send confirmation email")
    except Exception as e:
        print(f"❌ Error sending confirmation email: {str(e)}")
    print()
    
    # Test 2: Status Update Email
    print("📧 Test 2: Sending Donation Status Update Email")
    try:
        # Update donation status
        old_status = donation.status
        donation.status = 'completed'
        donation.verification_date = timezone.now()
        donation.save()
        
        success = send_donation_status_update_email(donation, old_status)
        if success:
            print("✅ Status update email sent successfully!")
        else:
            print("❌ Failed to send status update email")
    except Exception as e:
        print(f"❌ Error sending status update email: {str(e)}")
    print()
    
    # Test 3: Receipt Email
    print("📧 Test 3: Sending Donation Receipt Email")
    try:
        success = send_donation_receipt_email(donation)
        if success:
            print("✅ Receipt email sent successfully!")
        else:
            print("❌ Failed to send receipt email")
    except Exception as e:
        print(f"❌ Error sending receipt email: {str(e)}")
    print()
    
    # Clean up test data
    print("🧹 Cleaning up test data...")
    donation.delete()
    if created:
        campaign.delete()
        campaign_type.delete()
    print("✅ Test data cleaned up")
    print()
    
    print("🎉 Email testing completed!")
    print("=" * 50)
    print("📋 Summary:")
    print("- Confirmation emails are sent when donations are created")
    print("- Status update emails are sent when donation status changes")
    print("- Receipt emails are sent for completed donations")
    print("- All emails use the system's consistent design theme")
    print()
    print("💡 To test with real emails:")
    print("1. Update the test_email variable in this script")
    print("2. Ensure SMTP settings are configured in Django")
    print("3. Run: python test_donation_emails.py")

if __name__ == "__main__":
    test_donation_emails()
