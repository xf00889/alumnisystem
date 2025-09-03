#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from django.contrib.auth import get_user_model, authenticate
from django.db import transaction
from accounts.models import UserProfile

User = get_user_model()

def emergency_fix_admin():
    print("=== EMERGENCY ADMIN FIX ===")
    print("This script will force-create/update the admin user")
    
    username = 'admin'
    email = 'admin@admin.com'
    password = '123'
    
    try:
        with transaction.atomic():
            # Delete any existing admin user first
            existing_users = User.objects.filter(username=username)
            if existing_users.exists():
                print(f"Found {existing_users.count()} existing admin users. Deleting...")
                existing_users.delete()
                print("Deleted existing admin users.")
            
            # Create fresh admin user
            print("Creating new admin superuser...")
            admin_user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            print(f"✓ Created superuser: {admin_user.username}")
            print(f"  - Email: {admin_user.email}")
            print(f"  - Is active: {admin_user.is_active}")
            print(f"  - Is staff: {admin_user.is_staff}")
            print(f"  - Is superuser: {admin_user.is_superuser}")
            
            # Create user profile
            profile, created = UserProfile.objects.get_or_create(
                user=admin_user,
                defaults={
                    'first_name': 'Admin',
                    'last_name': 'User',
                    'phone_number': '+1234567890',
                    'address': 'Admin Address',
                    'city': 'Admin City',
                    'state': 'Admin State',
                    'zip_code': '12345',
                    'country': 'Admin Country',
                }
            )
            
            if created:
                print("✓ Created user profile")
            else:
                print("✓ User profile already exists")
            
            # Test authentication
            print("\n=== TESTING AUTHENTICATION ===")
            auth_user = authenticate(username=username, password=password)
            if auth_user:
                print("✓ Authentication successful!")
                print(f"  - Authenticated user: {auth_user.username}")
                print(f"  - User ID: {auth_user.id}")
            else:
                print("✗ Authentication failed!")
                return False
            
            # Test email authentication
            auth_user_email = authenticate(username=email, password=password)
            if auth_user_email:
                print("✓ Email authentication successful!")
            else:
                print("✗ Email authentication failed!")
            
            print("\n=== FINAL VERIFICATION ===")
            final_user = User.objects.get(username=username)
            print(f"Final user check:")
            print(f"  - Username: {final_user.username}")
            print(f"  - Email: {final_user.email}")
            print(f"  - Is active: {final_user.is_active}")
            print(f"  - Is staff: {final_user.is_staff}")
            print(f"  - Is superuser: {final_user.is_superuser}")
            print(f"  - Has profile: {hasattr(final_user, 'userprofile')}")
            
            if hasattr(final_user, 'userprofile'):
                profile = final_user.userprofile
                print(f"  - Profile first name: {profile.first_name}")
                print(f"  - Profile last name: {profile.last_name}")
            
            print("\n=== SUCCESS ===")
            print("Admin user has been successfully created/updated!")
            print("Login credentials:")
            print(f"  Username: {username}")
            print(f"  Email: {email}")
            print(f"  Password: {password}")
            
            return True
            
    except Exception as e:
        print(f"\n=== ERROR ===")
        print(f"Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = emergency_fix_admin()
    if success:
        print("\n🎉 Emergency fix completed successfully!")
        print("You should now be able to log in with admin/admin@admin.com/123")
    else:
        print("\n❌ Emergency fix failed. Check the error messages above.")
        sys.exit(1)