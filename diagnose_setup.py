#!/usr/bin/env python
"""
Diagnostic script to check setup issues
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from django.contrib.auth import get_user_model
from setup.models import SetupState
from django.contrib.sites.models import Site

User = get_user_model()

print("=" * 60)
print("SETUP DIAGNOSTIC REPORT")
print("=" * 60)

# Check database connection
print("\n1. Database Connection:")
try:
    User.objects.count()
    print("   ✓ Database connection OK")
except Exception as e:
    print(f"   ✗ Database error: {e}")

# Check existing users
print("\n2. Existing Users:")
users = User.objects.all()
if users.exists():
    for user in users:
        print(f"   - {user.username} (email: {user.email}, superuser: {user.is_superuser})")
else:
    print("   No users found")

# Check setup state
print("\n3. Setup State:")
try:
    setup_state = SetupState.objects.first()
    if setup_state:
        print(f"   Setup complete: {setup_state.is_complete}")
        print(f"   Completed at: {setup_state.completed_at}")
    else:
        print("   No setup state record found")
except Exception as e:
    print(f"   Error: {e}")

# Check Site configuration
print("\n4. Site Configuration:")
try:
    site = Site.objects.get(id=1)
    print(f"   Domain: {site.domain}")
    print(f"   Name: {site.name}")
except Exception as e:
    print(f"   Error: {e}")

# Check if we can create a test user
print("\n5. Test User Creation:")
try:
    test_username = "test_diagnostic_user"
    # Delete if exists
    User.objects.filter(username=test_username).delete()
    
    # Try to create
    test_user = User.objects.create_user(
        username=test_username,
        email="test@example.com",
        password="testpass123"
    )
    print(f"   ✓ Successfully created test user: {test_user.username}")
    
    # Clean up
    test_user.delete()
    print("   ✓ Successfully deleted test user")
except Exception as e:
    print(f"   ✗ Error creating test user: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
