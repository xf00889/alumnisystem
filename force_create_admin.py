#!/usr/bin/env python
"""
Force create admin superuser in production.
This script will create the admin user regardless of environment.
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile
from django.contrib.auth.hashers import make_password

def force_create_admin():
    """
    Force create admin superuser
    """
    print("=== Force Creating Admin Superuser ===")
    
    username = 'admin'
    email = 'admin@admin.com'
    password = '123'
    
    try:
        # Check if user already exists
        try:
            user = User.objects.get(username=username)
            print(f"User '{username}' already exists. Updating...")
            
            # Update existing user
            user.email = email
            user.is_active = True
            user.is_staff = True
            user.is_superuser = True
            user.set_password(password)
            user.save()
            
            print(f"✓ Updated existing user '{username}'")
            
        except User.DoesNotExist:
            # Create new user
            user = User.objects.create(
                username=username,
                email=email,
                is_active=True,
                is_staff=True,
                is_superuser=True
            )
            user.set_password(password)
            user.save()
            
            print(f"✓ Created new superuser '{username}'")
        
        # Ensure profile exists
        try:
            profile = Profile.objects.get(user=user)
            print("✓ Profile already exists")
        except Profile.DoesNotExist:
            profile = Profile.objects.create(
                user=user,
                first_name='Admin',
                last_name='User',
                phone_number='',
                address='',
                city='',
                state='',
                country='Philippines',
                postal_code='',
                date_of_birth=None,
                gender='',
                marital_status='',
                occupation='Administrator',
                company='NORSU',
                bio='System Administrator',
                registration_complete=True
            )
            print("✓ Created profile for admin user")
        
        # Verify the user can authenticate
        from django.contrib.auth import authenticate
        auth_user = authenticate(username=username, password=password)
        if auth_user:
            print("✓ Authentication test successful")
        else:
            print("✗ Authentication test failed")
            return False
        
        print()
        print("=== Admin User Details ===")
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"Is active: {user.is_active}")
        print(f"Is staff: {user.is_staff}")
        print(f"Is superuser: {user.is_superuser}")
        print(f"Password: {password}")
        print()
        print("=== SUCCESS ===")
        print("Admin superuser has been created/updated successfully!")
        print("You can now login with:")
        print(f"  Username: {username}")
        print(f"  Email: {email}")
        print(f"  Password: {password}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = force_create_admin()
    if not success:
        exit(1)