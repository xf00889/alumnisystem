#!/usr/bin/env python
"""
Test script to debug login issues
"""

import os
import sys
import django
from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

User = get_user_model()

def test_login_process():
    """Test the login process to identify issues"""
    print("=== Testing Login Process ===")
    
    # Create a test client with proper host
    client = Client(HTTP_HOST='127.0.0.1:8000')
    
    # Test 1: GET login page
    print("\n1. Testing GET /accounts/login/")
    try:
        response = client.get('/accounts/login/')
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: Expected 200, got {response.status_code}")
            print(f"Content: {response.content[:500]}")
    except Exception as e:
        print(f"Exception during GET login: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Create a test user if needed
    print("\n2. Creating test user")
    try:
        test_user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        if created:
            test_user.set_password('testpassword123')
            test_user.save()
            print("Test user created")
        else:
            print("Test user already exists")
            
        # Ensure user has a profile
        from accounts.models import Profile
        profile, created = Profile.objects.get_or_create(user=test_user)
        if created:
            print("Profile created for test user")
        else:
            print("Profile already exists for test user")
            
        # Check registration completion status
        print(f"Registration completed: {profile.has_completed_registration}")
        
        # For testing, mark registration as complete
        if not profile.has_completed_registration:
            profile.has_completed_registration = True
            profile.save()
            print("Marked registration as complete for testing")
            
    except Exception as e:
        print(f"Exception creating test user: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 3: POST login with valid credentials
    print("\n3. Testing POST /accounts/login/ with valid credentials")
    try:
        # First get the login page to get CSRF token
        response = client.get('/accounts/login/')
        csrf_token = None
        if 'csrfmiddlewaretoken' in response.content.decode():
            # Extract CSRF token from the form
            import re
            match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.content.decode())
            if match:
                csrf_token = match.group(1)
                print(f"CSRF token extracted: {csrf_token[:20]}...")
        
        # Prepare login data
        login_data = {
            'login': 'testuser',
            'password': 'testpassword123',
        }
        
        if csrf_token:
            login_data['csrfmiddlewaretoken'] = csrf_token
        
        # Attempt login
        response = client.post('/accounts/login/', login_data, follow=True)
        print(f"Status: {response.status_code}")
        print(f"Redirect chain: {response.redirect_chain}")
        
        if response.status_code != 200:
            print(f"Error: Expected 200, got {response.status_code}")
            print(f"Content: {response.content[:1000]}")
        else:
            print("Login appears successful")
            
    except Exception as e:
        print(f"Exception during POST login: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Check home page access
    print("\n4. Testing home page access after login")
    try:
        response = client.get('/')
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: Expected 200, got {response.status_code}")
            print(f"Content: {response.content[:500]}")
    except Exception as e:
        print(f"Exception accessing home page: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_login_process()