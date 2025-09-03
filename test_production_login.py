#!/usr/bin/env python
"""
Script to test login functionality that can be run in production environment.
This script will be deployed and can be executed via Render's shell access.
"""

import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from accounts.models import Profile
from django.contrib.auth.hashers import make_password, check_password

def test_production_login():
    print("=== Production Login Test ===")
    print(f"Environment: {'Production' if not settings.DEBUG else 'Development'}")
    print(f"Database: {settings.DATABASES['default']['NAME'][:50]}...")
    print()
    
    # Check superuser count
    superuser_count = User.objects.filter(is_superuser=True).count()
    print(f"Superusers in database: {superuser_count}")
    
    # Check for admin user
    admin_exists = User.objects.filter(username='admin').exists()
    print(f"Admin user exists: {admin_exists}")
    
    if admin_exists:
        admin_user = User.objects.get(username='admin')
        print(f"Admin user details:")
        print(f"  - Username: {admin_user.username}")
        print(f"  - Email: {admin_user.email}")
        print(f"  - Is active: {admin_user.is_active}")
        print(f"  - Is superuser: {admin_user.is_superuser}")
        print(f"  - Password hash starts with: {admin_user.password[:20]}...")
        
        # Test authentication
        auth_result = authenticate(username='admin', password='123')
        print(f"  - Authentication with 'admin'/'123': {'SUCCESS' if auth_result else 'FAILED'}")
        
        # Test email authentication
        email_auth_result = authenticate(username='admin@admin.com', password='123')
        print(f"  - Authentication with email: {'SUCCESS' if email_auth_result else 'FAILED'}")
        
        # Check profile
        try:
            profile = admin_user.profile
            print(f"  - Profile exists: True")
        except Profile.DoesNotExist:
            print(f"  - Profile exists: False")
            # Create profile if missing
            Profile.objects.create(user=admin_user)
            print(f"  - Profile created")
    else:
        print("Creating admin user...")
        try:
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@admin.com',
                password='123'
            )
            print(f"Admin user created successfully: {admin_user.username}")
            
            # Create profile
            profile, created = Profile.objects.get_or_create(user=admin_user)
            print(f"Profile {'created' if created else 'already exists'}")
            
        except Exception as e:
            print(f"Error creating admin user: {e}")
    
    print()
    
    # List all users (limited)
    total_users = User.objects.count()
    print(f"Total users: {total_users}")
    
    if total_users <= 5:
        for user in User.objects.all():
            print(f"  - {user.username} ({user.email}) - Super: {user.is_superuser}")
    
    print("\n=== Test Complete ===")

if __name__ == '__main__':
    test_production_login()