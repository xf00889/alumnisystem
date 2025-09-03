#!/usr/bin/env python
"""
Script to check production database connection and superuser status.
This can be run locally to test production database connectivity.
"""

import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')

# Set production environment variables for testing
os.environ['DATABASE_URL'] = input("Enter production DATABASE_URL (from Render dashboard): ")
os.environ['DJANGO_SUPERUSER_USERNAME'] = 'admin'
os.environ['DJANGO_SUPERUSER_EMAIL'] = 'admin@admin.com'
os.environ['DJANGO_SUPERUSER_PASSWORD'] = '123'

django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from accounts.models import Profile
from django.db import connection

def check_production_database():
    """
    Check production database connection and superuser status
    """
    print("=== Production Database Check ===")
    print()
    
    # Test database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✓ Database connection successful")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return
    
    print()
    
    # Check database type
    print(f"Database engine: {settings.DATABASES['default']['ENGINE']}")
    if 'DATABASE_URL' in os.environ:
        print("✓ Using production DATABASE_URL")
    else:
        print("✗ DATABASE_URL not set - using local database")
    
    print()
    
    # Check total users
    total_users = User.objects.count()
    print(f"Total users in database: {total_users}")
    
    # Check superusers
    superusers = User.objects.filter(is_superuser=True)
    print(f"Total superusers: {superusers.count()}")
    
    for user in superusers:
        print(f"  - {user.username} ({user.email}) - Active: {user.is_active}")
    
    print()
    
    # Check for admin user specifically
    try:
        admin_user = User.objects.get(username='admin')
        print("Admin user found:")
        print(f"  - Username: {admin_user.username}")
        print(f"  - Email: {admin_user.email}")
        print(f"  - Is active: {admin_user.is_active}")
        print(f"  - Is superuser: {admin_user.is_superuser}")
        print(f"  - Is staff: {admin_user.is_staff}")
        print(f"  - Date joined: {admin_user.date_joined}")
        print(f"  - Last login: {admin_user.last_login}")
        
        # Test authentication
        auth_result = authenticate(username='admin', password='123')
        if auth_result:
            print("  - Authentication: ✓ SUCCESS")
        else:
            print("  - Authentication: ✗ FAILED")
        
        # Check profile
        try:
            profile = Profile.objects.get(user=admin_user)
            print(f"  - Profile exists: ✓ YES")
            print(f"  - Registration complete: {getattr(profile, 'registration_complete', 'N/A')}")
        except Profile.DoesNotExist:
            print("  - Profile exists: ✗ NO")
        
    except User.DoesNotExist:
        print("✗ Admin user not found in production database")
        print("This means the create_superuser command did not run successfully")
    
    print()
    
    # List all users for debugging
    print("All users in database:")
    for user in User.objects.all():
        print(f"  - {user.username} ({user.email}) - Active: {user.is_active}, Super: {user.is_superuser}")
    
    print()
    print("=== Check Complete ===")

if __name__ == '__main__':
    try:
        check_production_database()
    except KeyboardInterrupt:
        print("\nCheck cancelled by user")
    except Exception as e:
        print(f"\nError during check: {e}")
        import traceback
        traceback.print_exc()