"""
Simple verification script to check Alumni Coordinator permissions.
Run this to verify the current state of permissions.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import Profile

User = get_user_model()

print("=" * 60)
print("ALUMNI COORDINATOR PERMISSION VERIFICATION")
print("=" * 60)

# Find all alumni coordinators
coordinators = User.objects.filter(profile__is_alumni_coordinator=True)

if not coordinators.exists():
    print("\n❌ No Alumni Coordinators found in the database.")
    print("   Create one using: python manage.py set_alumni_coordinator <email>")
else:
    print(f"\n✓ Found {coordinators.count()} Alumni Coordinator(s):\n")
    
    for coordinator in coordinators:
        print(f"  User: {coordinator.email}")
        print(f"  - is_staff: {coordinator.is_staff}")
        print(f"  - is_superuser: {coordinator.is_superuser}")
        print(f"  - is_alumni_coordinator: {coordinator.profile.is_alumni_coordinator}")
        print(f"  - is_hr: {coordinator.profile.is_hr}")
        print()
        
        # Check permissions
        print("  Permission Checks:")
        print(f"  - Can access admin dashboard: {coordinator.is_staff or coordinator.is_superuser}")
        print(f"  - Can manage roles: {coordinator.is_superuser}")
        print(f"  - Can toggle user status: {coordinator.is_superuser}")
        print()

# Check superusers
superusers = User.objects.filter(is_superuser=True)
print(f"✓ Found {superusers.count()} Superuser(s):\n")

for superuser in superusers:
    print(f"  User: {superuser.email}")
    print(f"  - is_staff: {superuser.is_staff}")
    print(f"  - is_superuser: {superuser.is_superuser}")
    print()

print("=" * 60)
print("PERMISSION MATRIX")
print("=" * 60)
print()
print("Role                  | Admin Dashboard | Manage Roles | Toggle Status")
print("----------------------|-----------------|--------------|---------------")
print("Alumni Coordinator    | ✓ YES           | ✗ NO         | ✗ NO")
print("Superuser             | ✓ YES           | ✓ YES        | ✓ YES")
print()
print("=" * 60)
print("TEMPLATE CONTEXT FLAGS")
print("=" * 60)
print()
print("For Alumni Coordinators, the following context flags should be:")
print("  - is_superuser: False")
print("  - can_modify_user: False")
print("  - can_manage_roles: False")
print("  - can_toggle_status: False")
print()
print("For Superusers, all flags should be: True")
print()
print("=" * 60)
print("TROUBLESHOOTING")
print("=" * 60)
print()
print("If Alumni Coordinators are seeing the 'Manage Roles' button:")
print("1. Clear browser cache (Ctrl+Shift+Delete)")
print("2. Hard refresh the page (Ctrl+F5)")
print("3. Check browser console for JavaScript errors")
print("4. Verify the user has is_staff=True (required for admin access)")
print()
print("If they get 403 errors:")
print("1. This is EXPECTED behavior - they shouldn't have access")
print("2. The button should be hidden by the template")
print("3. Clear cache and refresh to see the updated template")
print()
print("=" * 60)
