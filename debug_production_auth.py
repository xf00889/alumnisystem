#!/usr/bin/env python
import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from accounts.models import Profile
from django.contrib.auth.hashers import check_password

def debug_production_auth():
    print("=== Production Authentication Debug ===")
    print()
    
    # Check if any superusers exist
    superusers = User.objects.filter(is_superuser=True)
    print(f"Total superusers in database: {superusers.count()}")
    
    if superusers.exists():
        for user in superusers:
            print(f"  - Username: {user.username}, Email: {user.email}, Active: {user.is_active}")
            print(f"    Created: {user.date_joined}, Last login: {user.last_login}")
            print(f"    Has profile: {hasattr(user, 'profile') and user.profile is not None}")
    else:
        print("  No superusers found!")
    
    print()
    
    # Check specific admin user
    admin_username = 'admin'
    admin_email = 'admin@admin.com'
    
    try:
        admin_user = User.objects.get(username=admin_username)
        print(f"Admin user '{admin_username}' exists:")
        print(f"  - Email: {admin_user.email}")
        print(f"  - Is active: {admin_user.is_active}")
        print(f"  - Is superuser: {admin_user.is_superuser}")
        print(f"  - Is staff: {admin_user.is_staff}")
        print(f"  - Password hash: {admin_user.password[:50]}...")
        
        # Test password verification
        test_password = '123'
        password_valid = check_password(test_password, admin_user.password)
        print(f"  - Password '123' is valid: {password_valid}")
        
        # Test authentication
        auth_user = authenticate(username=admin_username, password=test_password)
        print(f"  - Authentication successful: {auth_user is not None}")
        
        # Test authentication with email
        auth_user_email = authenticate(username=admin_email, password=test_password)
        print(f"  - Authentication with email successful: {auth_user_email is not None}")
        
        # Check profile
        try:
            profile = admin_user.profile
            print(f"  - Profile exists: True")
            print(f"  - Registration complete: {getattr(profile, 'registration_complete', 'N/A')}")
        except Profile.DoesNotExist:
            print(f"  - Profile exists: False")
            
    except User.DoesNotExist:
        print(f"Admin user '{admin_username}' does not exist!")
        
        # Try to find user by email
        try:
            user_by_email = User.objects.get(email=admin_email)
            print(f"Found user with email '{admin_email}': {user_by_email.username}")
        except User.DoesNotExist:
            print(f"No user found with email '{admin_email}'")
    
    print()
    
    # List all users for debugging
    all_users = User.objects.all()
    print(f"Total users in database: {all_users.count()}")
    
    if all_users.count() <= 10:  # Only show if not too many
        for user in all_users:
            print(f"  - {user.username} ({user.email}) - Active: {user.is_active}, Super: {user.is_superuser}")
    else:
        print("  (Too many users to display)")
    
    print()
    
    # Check environment variables
    print("Environment variables:")
    print(f"  - DJANGO_SUPERUSER_USERNAME: {os.environ.get('DJANGO_SUPERUSER_USERNAME', 'Not set')}")
    print(f"  - DJANGO_SUPERUSER_EMAIL: {os.environ.get('DJANGO_SUPERUSER_EMAIL', 'Not set')}")
    print(f"  - DJANGO_SUPERUSER_PASSWORD: {'Set' if os.environ.get('DJANGO_SUPERUSER_PASSWORD') else 'Not set'}")
    
    print()
    print("=== Debug Complete ===")

if __name__ == '__main__':
    debug_production_auth()