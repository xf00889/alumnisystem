#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile

def check_existing_users():
    """Check what users exist in the database"""
    print("=== Checking Existing Users ===")
    
    users = User.objects.all()
    print(f"Total users in database: {users.count()}")
    print()
    
    if users.exists():
        print("Existing users:")
        for user in users:
            print(f"  - Username: {user.username}")
            print(f"    Email: {user.email}")
            print(f"    Is active: {user.is_active}")
            print(f"    Is staff: {user.is_staff}")
            print(f"    Is superuser: {user.is_superuser}")
            print(f"    Date joined: {user.date_joined}")
            
            # Check profile
            try:
                profile = Profile.objects.get(user=user)
                print(f"    Has profile: Yes (ID: {profile.id})")
            except Profile.DoesNotExist:
                print(f"    Has profile: No")
            print()
    else:
        print("No users found in database.")
        print()
        print("This suggests the superuser creation might not have run properly.")
        print("Let me check the environment variables for superuser creation...")
        
        # Check environment variables
        print("\n=== Environment Variables ===")
        env_vars = ['DJANGO_SUPERUSER_USERNAME', 'DJANGO_SUPERUSER_EMAIL', 'DJANGO_SUPERUSER_PASSWORD']
        for var in env_vars:
            value = os.environ.get(var, 'Not set')
            if 'PASSWORD' in var and value != 'Not set':
                value = '*' * len(value)  # Hide password
            print(f"{var}: {value}")

def create_test_superuser():
    """Create a test superuser if none exists"""
    print("\n=== Creating Test Superuser ===")
    
    if not User.objects.filter(is_superuser=True).exists():
        print("No superuser found. Creating test superuser...")
        
        try:
            user = User.objects.create_superuser(
                username='admin',
                email='admin@admin.com',
                password='123'
            )
            print(f"✓ Superuser created successfully:")
            print(f"  - Username: {user.username}")
            print(f"  - Email: {user.email}")
            print(f"  - ID: {user.id}")
            
            # Create profile if it doesn't exist
            profile, created = Profile.objects.get_or_create(user=user)
            if created:
                print(f"✓ Profile created for superuser (ID: {profile.id})")
            else:
                print(f"✓ Profile already exists for superuser (ID: {profile.id})")
                
        except Exception as e:
            print(f"✗ Error creating superuser: {e}")
    else:
        print("Superuser already exists.")

if __name__ == '__main__':
    print("Checking database users...")
    print("=" * 50)
    
    check_existing_users()
    create_test_superuser()
    
    print("\n" + "=" * 50)
    print("Check completed.")