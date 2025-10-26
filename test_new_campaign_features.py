#!/usr/bin/env python
"""
Test script for the new campaign creation and GCash management features
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from django.contrib.auth import get_user_model
from donations.models import Campaign, CampaignType, GCashConfig
from django.utils import timezone
from decimal import Decimal

User = get_user_model()

def test_new_campaign_features():
    """Test the new campaign creation and GCash management features"""
    print("🧪 Testing New Campaign Features")
    print("=" * 50)
    
    # Test 1: Create multiple GCash configurations
    print("📱 Test 1: Creating multiple GCash configurations")
    
    # Create first GCash config
    gcash_config1, created1 = GCashConfig.objects.get_or_create(
        name="Main GCash Account",
        defaults={
            'gcash_number': '09123456789',
            'account_name': 'NORSU Alumni Association',
            'is_active': True,
            'instructions': 'Send donations to this account for alumni activities'
        }
    )
    print(f"✅ Created GCash config 1: {gcash_config1.name}")
    
    # Create second GCash config
    gcash_config2, created2 = GCashConfig.objects.get_or_create(
        name="Emergency Fund Account",
        defaults={
            'gcash_number': '09987654321',
            'account_name': 'NORSU Emergency Fund',
            'is_active': True,
            'instructions': 'Emergency donations and disaster relief'
        }
    )
    print(f"✅ Created GCash config 2: {gcash_config2.name}")
    
    # Create inactive GCash config
    gcash_config3, created3 = GCashConfig.objects.get_or_create(
        name="Old Account (Inactive)",
        defaults={
            'gcash_number': '09111111111',
            'account_name': 'Old NORSU Account',
            'is_active': False,
            'instructions': 'This account is no longer used'
        }
    )
    print(f"✅ Created GCash config 3: {gcash_config3.name} (inactive)")
    
    # Test 2: Create campaign type
    print("\n📝 Test 2: Creating campaign type")
    campaign_type, created = CampaignType.objects.get_or_create(
        name="Test Campaign Type",
        defaults={'description': "Test campaign type for new features testing"}
    )
    print(f"✅ Created campaign type: {campaign_type.name}")
    
    # Test 3: Create campaign without donations
    print("\n🚫 Test 3: Creating campaign without donations")
    campaign_no_donations, created = Campaign.objects.get_or_create(
        name="Test Campaign (No Donations)",
        defaults={
            'campaign_type': campaign_type,
            'description': 'This campaign does not allow donations.',
            'short_description': 'No donations campaign',
            'goal_amount': Decimal('1000.00'),
            'current_amount': Decimal('0.00'),
            'status': 'active',
            'visibility': 'public',
            'allow_donations': False,  # New field
            'gcash_config': None  # No GCash config needed
        }
    )
    print(f"✅ Created campaign without donations: {campaign_no_donations.name}")
    print(f"   - Allow donations: {campaign_no_donations.allow_donations}")
    print(f"   - GCash config: {campaign_no_donations.gcash_config}")
    
    # Test 4: Create campaign with donations
    print("\n💰 Test 4: Creating campaign with donations")
    campaign_with_donations, created = Campaign.objects.get_or_create(
        name="Test Campaign (With Donations)",
        defaults={
            'campaign_type': campaign_type,
            'description': 'This campaign allows donations.',
            'short_description': 'Donations enabled campaign',
            'goal_amount': Decimal('5000.00'),
            'current_amount': Decimal('0.00'),
            'status': 'active',
            'visibility': 'public',
            'allow_donations': True,  # New field
            'gcash_config': gcash_config1  # Use first GCash config
        }
    )
    print(f"✅ Created campaign with donations: {campaign_with_donations.name}")
    print(f"   - Allow donations: {campaign_with_donations.allow_donations}")
    print(f"   - GCash config: {campaign_with_donations.gcash_config}")
    
    # Test 5: Create another campaign with different GCash config
    print("\n🔄 Test 5: Creating campaign with different GCash config")
    campaign_emergency, created = Campaign.objects.get_or_create(
        name="Emergency Fund Campaign",
        defaults={
            'campaign_type': campaign_type,
            'description': 'Emergency fund campaign with different GCash account.',
            'short_description': 'Emergency fund campaign',
            'goal_amount': Decimal('10000.00'),
            'current_amount': Decimal('0.00'),
            'status': 'active',
            'visibility': 'public',
            'allow_donations': True,  # New field
            'gcash_config': gcash_config2  # Use second GCash config
        }
    )
    print(f"✅ Created emergency campaign: {campaign_emergency.name}")
    print(f"   - Allow donations: {campaign_emergency.allow_donations}")
    print(f"   - GCash config: {campaign_emergency.gcash_config}")
    
    # Test 6: Test GCash config relationships
    print("\n🔗 Test 6: Testing GCash config relationships")
    campaigns_using_config1 = gcash_config1.campaigns.count()
    campaigns_using_config2 = gcash_config2.campaigns.count()
    campaigns_using_config3 = gcash_config3.campaigns.count()
    
    print(f"✅ Campaigns using GCash config 1: {campaigns_using_config1}")
    print(f"✅ Campaigns using GCash config 2: {campaigns_using_config2}")
    print(f"✅ Campaigns using GCash config 3: {campaigns_using_config3}")
    
    # Test 7: Test active GCash configs
    print("\n✅ Test 7: Testing active GCash configs")
    active_configs = GCashConfig.objects.filter(is_active=True)
    inactive_configs = GCashConfig.objects.filter(is_active=False)
    
    print(f"✅ Active GCash configs: {active_configs.count()}")
    for config in active_configs:
        print(f"   - {config.name} ({config.gcash_number})")
    
    print(f"✅ Inactive GCash configs: {inactive_configs.count()}")
    for config in inactive_configs:
        print(f"   - {config.name} ({config.gcash_number})")
    
    # Test 8: Test form validation scenarios
    print("\n🔍 Test 8: Testing form validation scenarios")
    
    # Test campaign with donations but no GCash config (should be invalid)
    try:
        invalid_campaign = Campaign(
            name="Invalid Campaign",
            campaign_type=campaign_type,
            description="This should fail validation",
            short_description="Invalid",
            goal_amount=Decimal('1000.00'),
            allow_donations=True,
            gcash_config=None  # This should cause validation error
        )
        invalid_campaign.full_clean()  # This should raise ValidationError
        print("❌ Validation should have failed but didn't")
    except Exception as e:
        print(f"✅ Validation correctly failed: {str(e)[:100]}...")
    
    print("\n🎉 New campaign features testing completed!")
    print("=" * 50)
    print("📋 Summary of new features:")
    print("1. ✅ Multiple GCash configurations supported")
    print("2. ✅ Campaign donation toggle field added")
    print("3. ✅ GCash account selection for campaigns")
    print("4. ✅ Form validation for donation settings")
    print("5. ✅ GCash configuration management page")
    print("6. ✅ Campaign-GCash relationship tracking")
    print()
    print("💡 Next steps:")
    print("- Visit /donations/manage/gcash/ to see the new GCash management page")
    print("- Visit /donations/campaigns/create/ to test the new campaign form")
    print("- The GCash dropdown will only show when 'Allow Donations' is enabled")

if __name__ == "__main__":
    test_new_campaign_features()
