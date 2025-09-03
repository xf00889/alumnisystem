#!/usr/bin/env python
"""
Create a direct admin login bypass that doesn't use django-allauth.
This creates a simple Django admin superuser that can access /admin/ directly.
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from accounts.models import Profile
from django.db import transaction

def create_direct_admin_login():
    """
    Create admin user that bypasses django-allauth completely
    """
    print("=== Creating Direct Admin Login ===\n")
    
    username = 'admin'
    email = 'admin@admin.com'
    password = '123'
    
    try:
        with transaction.atomic():
            # Delete any existing admin users to start fresh
            existing_admins = User.objects.filter(username=username)
            if existing_admins.exists():
                print(f"Deleting {existing_admins.count()} existing admin user(s)...")
                existing_admins.delete()
            
            # Create new superuser
            print("Creating new admin superuser...")
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            
            # Ensure user is active and has all permissions
            user.is_active = True
            user.is_staff = True
            user.is_superuser = True
            user.save()
            
            print(f"✓ Created superuser: {username}")
            print(f"  - Email: {email}")
            print(f"  - Is active: {user.is_active}")
            print(f"  - Is staff: {user.is_staff}")
            print(f"  - Is superuser: {user.is_superuser}")
            
            # Create or update profile
            try:
                profile, created = Profile.objects.get_or_create(
                    user=user,
                    defaults={
                        'first_name': 'Admin',
                        'last_name': 'User',
                        'phone_number': '',
                        'address': '',
                        'city': '',
                        'state': '',
                        'country': 'Philippines',
                        'postal_code': '',
                        'date_of_birth': None,
                        'gender': '',
                        'marital_status': '',
                        'occupation': 'System Administrator',
                        'company': 'NORSU',
                        'bio': 'System Administrator Account',
                        'registration_complete': True
                    }
                )
                
                if created:
                    print("✓ Created new profile for admin user")
                else:
                    # Update existing profile
                    profile.registration_complete = True
                    profile.save()
                    print("✓ Updated existing profile for admin user")
                    
            except Exception as e:
                print(f"⚠ Warning: Could not create/update profile: {e}")
                print("  This won't prevent admin login, but may cause issues in the main app")
            
            # Test authentication
            print("\nTesting authentication...")
            auth_user = authenticate(username=username, password=password)
            if auth_user:
                print("✓ Authentication test successful")
                print(f"  - Authenticated user ID: {auth_user.id}")
                print(f"  - Can access admin: {auth_user.is_staff and auth_user.is_superuser}")
            else:
                print("✗ Authentication test failed")
                return False
            
            print("\n=== SUCCESS ===\n")
            print("Direct admin login has been created successfully!\n")
            print("LOGIN INSTRUCTIONS:")
            print("1. Go to: https://your-app-url.onrender.com/admin/")
            print("2. Use these credentials:")
            print(f"   Username: {username}")
            print(f"   Password: {password}")
            print("\nThis bypasses django-allauth and goes directly to Django admin.")
            print("\nIf you still can't login, the issue might be:")
            print("- Database connection problems")
            print("- Session/cookie issues")
            print("- CSRF token problems")
            print("- Server configuration issues")
            
            return True
            
    except Exception as e:
        print(f"✗ Error creating direct admin login: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = create_direct_admin_login()
    if not success:
        exit(1)