#!/usr/bin/env python
"""
Manual script to fix CMS data in production
Run this script on your production server to populate missing CMS data
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from django.core.management import call_command
from cms.models import SiteConfig

def main():
    print("🔧 Fixing CMS data in production...")
    
    # Check if CMS data exists
    if SiteConfig.objects.exists():
        print("✅ CMS data already exists")
        print("Current CMS data:")
        site_config = SiteConfig.objects.first()
        print(f"  - Site Name: {site_config.site_name}")
        print(f"  - Site Tagline: {site_config.site_tagline}")
        print(f"  - Contact Email: {site_config.contact_email}")
        
        response = input("\nDo you want to repopulate CMS data? (y/N): ")
        if response.lower() != 'y':
            print("❌ Operation cancelled")
            return
    else:
        print("⚠️ No CMS data found")
    
    try:
        # Populate CMS data
        print("\n📝 Populating CMS data...")
        call_command('populate_cms_data')
        
        # Verify the data
        print("\n🔍 Verifying CMS data...")
        from cms.models import *
        
        print(f"✅ SiteConfig: {SiteConfig.objects.count()}")
        print(f"✅ PageSection: {PageSection.objects.count()}")
        print(f"✅ ContactInfo: {ContactInfo.objects.count()}")
        print(f"✅ FAQ: {FAQ.objects.count()}")
        print(f"✅ StaffMember: {StaffMember.objects.count()}")
        print(f"✅ Feature: {Feature.objects.count()}")
        print(f"✅ Testimonial: {Testimonial.objects.count()}")
        print(f"✅ TimelineItem: {TimelineItem.objects.count()}")
        
        print("\n🎉 CMS data population completed successfully!")
        print("Your CMS dashboard should now show all the data correctly.")
        
    except Exception as e:
        print(f"❌ Error populating CMS data: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
