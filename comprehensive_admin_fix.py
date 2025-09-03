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
from django.contrib.auth.hashers import make_password, check_password
from accounts.models import UserProfile
from django.db import transaction
from django.conf import settings

User = get_user_model()

def comprehensive_admin_fix():
    print("=== COMPREHENSIVE ADMIN FIX SCRIPT ===")
    print(f"Django settings module: {settings.SETTINGS_MODULE}")
    print(f"Database: {settings.DATABASES['default']['ENGINE']}")
    
    # Check environment variables
    print("\n=== ENVIRONMENT VARIABLES ===")
    env_vars = ['DJANGO_SUPERUSER_USERNAME', 'DJANGO_SUPERUSER_EMAIL', 'DJANGO_SUPERUSER_PASSWORD']
    for var in env_vars:
        value = os.environ.get(var, 'NOT SET')
        print(f"{var}: {'SET' if value != 'NOT SET' else 'NOT SET'}")
    
    # Database connection test
    print("\n=== DATABASE CONNECTION TEST ===")
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✓ Database connection successful")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return
    
    # Check existing users
    print("\n=== EXISTING USERS ===")
    users = User.objects.all()
    print(f"Total users: {users.count()}")
    for user in users:
        print(f"- {user.username} ({user.email}) - Active: {user.is_active}, Staff: {user.is_staff}, Superuser: {user.is_superuser}")
    
    # Force create/update admin user
    print("\n=== FORCE CREATE/UPDATE ADMIN USER ===")
    admin_username = 'admin'
    admin_email = 'admin@admin.com'
    admin_password = '123'
    
    try:
        with transaction.atomic():
            # Delete existing admin user if exists
            existing_admin = User.objects.filter(username=admin_username).first()
            if existing_admin:
                print(f"Deleting existing admin user: {existing_admin.username}")
                existing_admin.delete()
            
            # Create new admin user
            admin_user = User.objects.create_user(
                username=admin_username,
                email=admin_email,
                password=admin_password,
                is_staff=True,
                is_superuser=True,
                is_active=True
            )
            print(f"✓ Created admin user: {admin_user.username}")
            
            # Create or update profile
            profile, created = UserProfile.objects.get_or_create(
                user=admin_user,
                defaults={
                    'first_name': 'Admin',
                    'last_name': 'User',
                    'registration_complete': True
                }
            )
            if created:
                print("✓ Created admin user profile")
            else:
                profile.registration_complete = True
                profile.save()
                print("✓ Updated admin user profile")
            
    except Exception as e:
        print(f"✗ Error creating admin user: {e}")
        return
    
    # Verify admin user
    print("\n=== ADMIN USER VERIFICATION ===")
    try:
        admin_user = User.objects.get(username=admin_username)
        print(f"Username: {admin_user.username}")
        print(f"Email: {admin_user.email}")
        print(f"Is active: {admin_user.is_active}")
        print(f"Is staff: {admin_user.is_staff}")
        print(f"Is superuser: {admin_user.is_superuser}")
        print(f"Password hash: {admin_user.password[:50]}...")
        
        # Check password
        password_valid = check_password(admin_password, admin_user.password)
        print(f"Password valid: {password_valid}")
        
        # Test authentication
        auth_user = authenticate(username=admin_username, password=admin_password)
        print(f"Authentication successful: {auth_user is not None}")
        
        # Check profile
        try:
            profile = admin_user.userprofile
            print(f"Profile exists: True")
            print(f"Registration complete: {profile.registration_complete}")
        except UserProfile.DoesNotExist:
            print(f"Profile exists: False")
            
    except User.DoesNotExist:
        print("✗ Admin user not found after creation")
        return
    
    # Test login with email
    print("\n=== EMAIL LOGIN TEST ===")
    try:
        auth_user = authenticate(username=admin_email, password=admin_password)
        print(f"Email authentication successful: {auth_user is not None}")
        if auth_user:
            print(f"Authenticated user: {auth_user.username} ({auth_user.email})")
    except Exception as e:
        print(f"Email authentication error: {e}")
    
    # Check authentication backends
    print("\n=== AUTHENTICATION BACKENDS ===")
    for backend in settings.AUTHENTICATION_BACKENDS:
        print(f"- {backend}")
    
    # Check allauth settings
    print("\n=== ALLAUTH SETTINGS ===")
    allauth_settings = [
        'ACCOUNT_AUTHENTICATION_METHOD',
        'ACCOUNT_EMAIL_REQUIRED',
        'ACCOUNT_USERNAME_REQUIRED',
        'LOGIN_URL',
        'LOGIN_REDIRECT_URL'
    ]
    for setting in allauth_settings:
        value = getattr(settings, setting, 'NOT SET')
        print(f"{setting}: {value}")
    
    print("\n=== SCRIPT COMPLETED ===")
    print("Admin credentials:")
    print(f"Username: {admin_username}")
    print(f"Email: {admin_email}")
    print(f"Password: {admin_password}")
    print("\nTry logging in with either username or email.")

if __name__ == '__main__':
    comprehensive_admin_fix()