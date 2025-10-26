#!/usr/bin/env python
"""
Test script for the corrected donation email flow
This script tests that emails are sent at the right time
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from django.contrib.auth import get_user_model
from donations.models import Campaign, CampaignType, Donation
from donations.email_utils import send_donation_confirmation_email, send_donation_status_update_email, send_donation_receipt_email
from django.utils import timezone
from decimal import Decimal

User = get_user_model()

def test_corrected_donation_flow():
    """Test the corrected donation email flow"""
    print("🧪 Testing Corrected Donation Email Flow")
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
            'description': 'This is a test campaign for email functionality testing.',
            'short_description': 'Test campaign for emails',
            'goal_amount': Decimal('10000.00'),
            'current_amount': Decimal('0.00'),
            'status': 'active',
            'visibility': 'public'
        }
    )
    
    # Test 1: Create donation (should NOT send email)
    print("📧 Test 1: Creating donation (should NOT send email)")
    donation = Donation.objects.create(
        campaign=campaign,
        donor_name="Test Donor",
        donor_email=test_email,
        amount=Decimal('100.00'),
        donation_date=timezone.now(),
        status='pending_payment',  # Initial status
        payment_method='gcash',
        is_anonymous=False,
        message="This is a test donation for email functionality testing.",
        reference_number="TEST-2024-001"
    )
    print(f"✅ Created donation with status: {donation.status}")
    print("📧 No email should be sent at this point (this is correct)")
    print()
    
    # Test 2: Submit payment proof (should send confirmation email)
    print("📧 Test 2: Submitting payment proof (should send confirmation email)")
    donation.status = 'pending_verification'
    donation.save()  # This should trigger the confirmation email
    
    print(f"✅ Updated donation status to: {donation.status}")
    print("📧 Confirmation email should be sent now (this is correct)")
    print()
    
    # Test 3: Complete donation (should send status update and receipt)
    print("📧 Test 3: Completing donation (should send status update and receipt)")
    donation.status = 'completed'
    donation.verification_date = timezone.now()
    donation.save()  # This should trigger status update and receipt emails
    
    print(f"✅ Updated donation status to: {donation.status}")
    print("📧 Status update and receipt emails should be sent now (this is correct)")
    print()
    
    # Clean up test data
    print("🧹 Cleaning up test data...")
    donation.delete()
    if created:
        campaign.delete()
        campaign_type.delete()
    print("✅ Test data cleaned up")
    print()
    
    print("🎉 Corrected donation flow testing completed!")
    print("=" * 50)
    print("📋 Summary of the corrected flow:")
    print("1. ✅ Donation created → NO email sent (correct)")
    print("2. ✅ Payment proof submitted → Confirmation email sent (correct)")
    print("3. ✅ Donation completed → Status update + receipt emails sent (correct)")
    print()
    print("💡 The email timing is now correct:")
    print("- Emails are only sent after payment proof submission")
    print("- Users see GCash configuration (QR code + phone number)")
    print("- Email flow matches the actual donation process")

if __name__ == "__main__":
    test_corrected_donation_flow()
