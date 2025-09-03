#!/usr/bin/env python
"""
Script to verify superuser creation in production.
This script should be run on the Render platform to check production database.
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from accounts.models import Profile
from django.db import connection
from django.conf import settings

def verify_production_superuser():
    """
    Verify superuser exists and can authenticate in production
    """
    print("=== Production Superuser Verification ===")
    print()
    
    # Check environment
    print("Environment check:")
    print(f"  - DEBUG: {settings.DEBUG}")
    print(f"  - DATABASE_URL set: {'DATABASE_URL' in os.environ}")
    print(f"  - Database engine: {settings.DATABASES['default']['ENGINE']}")
    
    # Check environment variables for superuser
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@admin.com')
    password_set = bool(os.environ.get('DJANGO_SUPERUSER_PASSWORD'))
    
    print(f"  - DJANGO_SUPERUSER_USERNAME: {username}")
    print(f"  - DJANGO_SUPERUSER_EMAIL: {email}")
    print(f"  - DJANGO_SUPERUSER_PASSWORD: {'Set' if password_set else 'Not set'}")
    print()
    
    # Test database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✓ Database connection successful")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False
    
    print()
    
    # Check users
    total_users = User.objects.count()
    superuser_count = User.objects.filter(is_superuser=True).count()
    
    print(f"Database statistics:")
    print(f"  - Total users: {total_users}")
    print(f"  - Superusers: {superuser_count}")
    print()
    
    # Check for admin user
    try:
        admin_user = User.objects.get(username=username)
        print(f"✓ User '{username}' found in database")
        print(f"  - Email: {admin_user.email}")
        print(f"  - Is active: {admin_user.is_active}")
        print(f"  - Is superuser: {admin_user.is_superuser}")
        print(f"  - Is staff: {admin_user.is_staff}")
        print(f"  - Date joined: {admin_user.date_joined}")
        print(f"  - Last login: {admin_user.last_login}")
        
        # Test authentication if password is available
        if password_set:
            password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
            auth_result = authenticate(username=username, password=password)
            if auth_result:
                print("  - Authentication test: ✓ SUCCESS")
            else:
                print("  - Authentication test: ✗ FAILED")
                
                # Try with email
                auth_result = authenticate(username=email, password=password)
                if auth_result:
                    print("  - Authentication with email: ✓ SUCCESS")
                else:
                    print("  - Authentication with email: ✗ FAILED")
        else:
            print("  - Authentication test: SKIPPED (password not available)")
        
        # Check profile
        try:
            profile = Profile.objects.get(user=admin_user)
            print("  - Profile: ✓ EXISTS")
            if hasattr(profile, 'registration_complete'):
                print(f"  - Registration complete: {profile.registration_complete}")
        except Profile.DoesNotExist:
            print("  - Profile: ✗ MISSING")
        
        return True
        
    except User.DoesNotExist:
        print(f"✗ User '{username}' not found in production database")
        print("This indicates the create_superuser command did not run successfully")
        print()
        print("Troubleshooting steps:")
        print("1. Check Render deployment logs for create_superuser command output")
        print("2. Verify environment variables are set correctly")
        print("3. Manually run: python manage.py create_superuser")
        return False
    
    except Exception as e:
        print(f"✗ Error checking user: {e}")
        return False

def list_all_users():
    """
    List all users for debugging
    """
    print("\n=== All Users in Database ===")
    users = User.objects.all()
    if users.exists():
        for user in users:
            print(f"  - {user.username} ({user.email})")
            print(f"    Active: {user.is_active}, Super: {user.is_superuser}, Staff: {user.is_staff}")
    else:
        print("  No users found in database")
    print()

if __name__ == '__main__':
    try:
        success = verify_production_superuser()
        list_all_users()
        
        if success:
            print("=== Verification Complete: SUCCESS ===")
            print("The superuser exists and should be able to login.")
            print("If login still fails, check:")
            print("1. Browser cache and cookies")
            print("2. Network connectivity")
            print("3. CSRF token issues")
        else:
            print("=== Verification Complete: FAILED ===")
            print("The superuser was not found or has issues.")
            print("Run the create_superuser management command manually.")
            
    except Exception as e:
        print(f"\nError during verification: {e}")
        import traceback
        traceback.print_exc()