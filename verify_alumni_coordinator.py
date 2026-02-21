"""
Verification script for Alumni Coordinator role implementation
Run this script to verify that the Alumni Coordinator role is properly configured
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import Profile
from django.conf import settings

User = get_user_model()

def verify_implementation():
    """Verify that the Alumni Coordinator role is properly implemented"""
    
    print("=" * 70)
    print("ALUMNI COORDINATOR ROLE - VERIFICATION")
    print("=" * 70)
    print()
    
    # Check 1: Profile model has the field
    print("✓ Check 1: Profile model field")
    try:
        profile_fields = [f.name for f in Profile._meta.get_fields()]
        if 'is_alumni_coordinator' in profile_fields:
            print("  ✓ is_alumni_coordinator field exists in Profile model")
        else:
            print("  ✗ is_alumni_coordinator field NOT found in Profile model")
            return False
    except Exception as e:
        print(f"  ✗ Error checking Profile model: {e}")
        return False
    
    # Check 2: Context processor is configured
    print("\n✓ Check 2: Context processor configuration")
    try:
        context_processors = settings.TEMPLATES[0]['OPTIONS']['context_processors']
        if 'core.context_processors.user_role_context' in context_processors:
            print("  ✓ user_role_context processor is configured")
        else:
            print("  ✗ user_role_context processor NOT configured")
            print("  Add 'core.context_processors.user_role_context' to TEMPLATES")
            return False
    except Exception as e:
        print(f"  ✗ Error checking context processors: {e}")
        return False
    
    # Check 3: Decorators file exists
    print("\n✓ Check 3: Access control decorators")
    try:
        from core.decorators import (
            superuser_required,
            staff_or_coordinator_required,
            system_config_required
        )
        print("  ✓ All decorators imported successfully")
    except ImportError as e:
        print(f"  ✗ Error importing decorators: {e}")
        return False
    
    # Check 4: Management command exists
    print("\n✓ Check 4: Management command")
    try:
        from accounts.management.commands.set_alumni_coordinator import Command
        print("  ✓ set_alumni_coordinator command exists")
    except ImportError as e:
        print(f"  ✗ Error importing management command: {e}")
        return False
    
    # Check 5: Test with a user (if any exist)
    print("\n✓ Check 5: Database functionality")
    try:
        user_count = User.objects.count()
        if user_count > 0:
            # Get first user
            test_user = User.objects.first()
            profile, created = Profile.objects.get_or_create(user=test_user)
            
            # Test setting the field
            original_value = profile.is_alumni_coordinator
            profile.is_alumni_coordinator = True
            profile.save()
            profile.refresh_from_db()
            
            if profile.is_alumni_coordinator:
                print(f"  ✓ Successfully set is_alumni_coordinator=True for {test_user.username}")
            else:
                print(f"  ✗ Failed to set is_alumni_coordinator for {test_user.username}")
                return False
            
            # Restore original value
            profile.is_alumni_coordinator = original_value
            profile.save()
            print(f"  ✓ Restored original value for {test_user.username}")
        else:
            print("  ⚠ No users in database to test with")
    except Exception as e:
        print(f"  ✗ Error testing database functionality: {e}")
        return False
    
    # Check 6: Count current coordinators
    print("\n✓ Check 6: Current coordinators")
    try:
        coordinator_count = Profile.objects.filter(is_alumni_coordinator=True).count()
        print(f"  ℹ Current Alumni Coordinators: {coordinator_count}")
        
        if coordinator_count > 0:
            coordinators = Profile.objects.filter(is_alumni_coordinator=True).select_related('user')
            print("  Coordinators:")
            for profile in coordinators:
                print(f"    - {profile.user.username} ({profile.user.email})")
    except Exception as e:
        print(f"  ✗ Error counting coordinators: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("✓ ALL CHECKS PASSED - Alumni Coordinator role is properly configured!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Assign the role: python manage.py set_alumni_coordinator <username>")
    print("2. Test by logging in as the coordinator")
    print("3. Verify system config items are hidden in the sidebar")
    print()
    
    return True

if __name__ == '__main__':
    try:
        verify_implementation()
    except Exception as e:
        print(f"\n✗ Verification failed with error: {e}")
        import traceback
        traceback.print_exc()
