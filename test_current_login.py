#!/usr/bin/env python
import os
import sys
import django
from django.test import Client
from django.contrib.auth import authenticate
from django.urls import reverse

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile

def test_login_credentials():
    """Test login with the provided credentials"""
    print("=== Testing Login Credentials ===")
    
    # Test credentials
    username = 'admin'
    email = 'admin@admin.com'
    password = '123'
    
    print(f"Testing with username: {username}")
    print(f"Testing with email: {email}")
    print(f"Testing with password: {password}")
    print()
    
    # Check if user exists
    try:
        user = User.objects.get(username=username)
        print(f"✓ User '{username}' exists in database")
        print(f"  - ID: {user.id}")
        print(f"  - Email: {user.email}")
        print(f"  - Is active: {user.is_active}")
        print(f"  - Is staff: {user.is_staff}")
        print(f"  - Is superuser: {user.is_superuser}")
        print(f"  - Last login: {user.last_login}")
        print(f"  - Date joined: {user.date_joined}")
        
        # Check if user has a profile
        try:
            profile = Profile.objects.get(user=user)
            print(f"  - Has profile: Yes")
            print(f"  - Profile ID: {profile.id}")
            # Check if profile has registration_complete field
            if hasattr(profile, 'registration_complete'):
                print(f"  - Registration complete: {profile.registration_complete}")
            else:
                print(f"  - Registration complete field: Not found")
        except Profile.DoesNotExist:
            print(f"  - Has profile: No")
        
    except User.DoesNotExist:
        print(f"✗ User '{username}' does not exist in database")
        return False
    
    print()
    
    # Test authentication
    print("Testing authentication...")
    auth_user = authenticate(username=username, password=password)
    if auth_user:
        print(f"✓ Authentication successful for '{username}'")
        print(f"  - Authenticated user ID: {auth_user.id}")
    else:
        print(f"✗ Authentication failed for '{username}'")
        
        # Try with email as username
        print(f"Trying authentication with email as username...")
        auth_user = authenticate(username=email, password=password)
        if auth_user:
            print(f"✓ Authentication successful with email '{email}'")
        else:
            print(f"✗ Authentication failed with email '{email}'")
    
    print()
    
    # Test login via web client
    print("Testing login via web client...")
    from django.test import override_settings
    
    # Override ALLOWED_HOSTS for testing
    with override_settings(ALLOWED_HOSTS=['testserver', 'localhost', '127.0.0.1']):
        client = Client()
        
        # Get login page
        login_url = '/accounts/login/'  # Django-allauth login URL
        try:
            response = client.get(login_url)
            print(f"GET {login_url}: {response.status_code}")
            
            if response.status_code == 200:
                # Try POST login
                login_data = {
                    'login': username,  # django-allauth uses 'login' field
                    'password': password,
                }
                
                response = client.post(login_url, login_data, follow=True)
                print(f"POST {login_url}: {response.status_code}")
                print(f"Final URL after redirects: {response.request['PATH_INFO'] if response.request else 'N/A'}")
                
                if response.status_code == 200:
                    # Check if login was successful by looking for user in session
                    if '_auth_user_id' in client.session:
                        print(f"✓ Login successful - User ID in session: {client.session['_auth_user_id']}")
                    else:
                        print(f"✗ Login failed - No user ID in session")
                        print(f"Response content preview: {response.content[:500].decode('utf-8', errors='ignore')}")
                else:
                    print(f"✗ Login request failed with status {response.status_code}")
            else:
                print(f"✗ Could not access login page - Status: {response.status_code}")
                
        except Exception as e:
            print(f"✗ Error during web client test: {e}")
    
    print()
    return True

def check_password_hashers():
    """Check if password hashers are properly configured"""
    print("=== Checking Password Hashers ===")
    
    from django.conf import settings
    from django.contrib.auth.hashers import get_hashers_by_algorithm
    
    print("Configured password hashers:")
    for hasher_path in settings.PASSWORD_HASHERS:
        print(f"  - {hasher_path}")
    
    print()
    
    # Test Argon2 specifically
    try:
        argon2_hashers = get_hashers_by_algorithm()
        if 'argon2' in argon2_hashers:
            print("✓ Argon2 password hasher is available")
        else:
            print("✗ Argon2 password hasher is not available")
    except Exception as e:
        print(f"✗ Error checking Argon2 hasher: {e}")
    
    print()

if __name__ == '__main__':
    print("Testing current login issue...")
    print("=" * 50)
    
    check_password_hashers()
    test_login_credentials()
    
    print("=" * 50)
    print("Test completed.")