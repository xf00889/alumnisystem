#!/usr/bin/env python
"""
Quick script to fix SSO site configuration
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

print("Fixing SSO configuration...")
print("=" * 60)

# Get or create site
site, created = Site.objects.get_or_create(
    pk=1,
    defaults={
        'domain': '127.0.0.1:8000',
        'name': 'NORSU Alumni (Local)'
    }
)

if not created:
    # Update existing site
    site.domain = '127.0.0.1:8000'
    site.name = 'NORSU Alumni (Local)'
    site.save()
    print(f"✓ Updated site: {site.domain}")
else:
    print(f"✓ Created site: {site.domain}")

# Get Google SocialApp
try:
    google_app = SocialApp.objects.get(provider='google')
    print(f"✓ Found Google SocialApp")
    
    # Clear and re-add sites
    google_app.sites.clear()
    google_app.sites.add(site)
    print(f"✓ Associated site with Google SocialApp")
    
    # Verify
    sites = list(google_app.sites.all())
    print(f"✓ Google SocialApp sites: {[s.domain for s in sites]}")
    
except SocialApp.DoesNotExist:
    print("✗ Google SocialApp not found!")
    print("  Please configure SSO in the admin panel first")

print("=" * 60)
print("Done! Try SSO login again.")
