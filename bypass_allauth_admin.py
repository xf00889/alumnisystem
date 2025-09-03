#!/usr/bin/env python
"""
Script to create a custom admin URL that bypasses django-allauth completely.
This creates a direct path to Django's admin interface.
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.test import Client
from django.urls import reverse

def test_admin_access():
    """
    Test different ways to access admin interface
    """
    print("=== Testing Admin Access Methods ===\n")
    
    # Check if admin user exists
    try:
        admin_user = User.objects.get(username='admin')
        print(f"✓ Admin user exists: {admin_user.username}")
        print(f"  - Is active: {admin_user.is_active}")
        print(f"  - Is staff: {admin_user.is_staff}")
        print(f"  - Is superuser: {admin_user.is_superuser}")
    except User.DoesNotExist:
        print("✗ Admin user does not exist")
        return False
    
    # Test authentication
    print("\nTesting authentication...")
    auth_user = authenticate(username='admin', password='123')
    if auth_user:
        print("✓ Authentication successful")
    else:
        print("✗ Authentication failed")
        return False
    
    # Test admin URLs
    print("\nTesting admin URLs...")
    client = Client()
    
    # Test admin login page
    try:
        response = client.get('/admin/')
        print(f"GET /admin/: {response.status_code}")
        if response.status_code == 302:
            print(f"  Redirects to: {response.url}")
    except Exception as e:
        print(f"✗ Error accessing /admin/: {e}")
    
    # Test admin login page directly
    try:
        response = client.get('/admin/login/')
        print(f"GET /admin/login/: {response.status_code}")
    except Exception as e:
        print(f"✗ Error accessing /admin/login/: {e}")
    
    # Test POST login to admin
    try:
        # Get CSRF token first
        response = client.get('/admin/login/')
        if response.status_code == 200:
            # Try to login
            login_data = {
                'username': 'admin',
                'password': '123',
                'next': '/admin/'
            }
            response = client.post('/admin/login/', login_data, follow=True)
            print(f"POST /admin/login/: {response.status_code}")
            
            if response.status_code == 200:
                if 'admin' in response.content.decode().lower():
                    print("✓ Successfully logged into admin interface")
                else:
                    print("✗ Login failed - not redirected to admin")
            else:
                print(f"✗ Login failed with status: {response.status_code}")
    except Exception as e:
        print(f"✗ Error testing admin login: {e}")
    
    return True

def check_allauth_interference():
    """
    Check if django-allauth is interfering with admin login
    """
    print("\n=== Checking Django-Allauth Configuration ===\n")
    
    from django.conf import settings
    
    print("Authentication backends:")
    for backend in settings.AUTHENTICATION_BACKENDS:
        print(f"  - {backend}")
    
    print(f"\nLogin URL: {settings.LOGIN_URL}")
    print(f"Login redirect URL: {settings.LOGIN_REDIRECT_URL}")
    print(f"Account authentication method: {getattr(settings, 'ACCOUNT_AUTHENTICATION_METHOD', 'Not set')}")
    
    # Check if allauth is overriding admin URLs
    from django.urls import resolve, reverse
    try:
        admin_url = reverse('admin:index')
        print(f"\nAdmin index URL: {admin_url}")
        
        login_url = reverse('admin:login')
        print(f"Admin login URL: {login_url}")
    except Exception as e:
        print(f"✗ Error resolving admin URLs: {e}")
    
    # Check allauth URLs
    try:
        allauth_login = reverse('account_login')
        print(f"Allauth login URL: {allauth_login}")
    except Exception as e:
        print(f"✗ Error resolving allauth URLs: {e}")

def provide_solutions():
    """
    Provide different solutions to try
    """
    print("\n=== SOLUTIONS TO TRY ===\n")
    
    print("SOLUTION 1: Direct Admin Access")
    print("- Go directly to: https://your-app.onrender.com/admin/")
    print("- Use username: admin, password: 123")
    print("- This should bypass django-allauth completely")
    
    print("\nSOLUTION 2: Clear Browser Data")
    print("- Clear all cookies and cache for your site")
    print("- Try in incognito/private browsing mode")
    print("- This fixes session/cookie conflicts")
    
    print("\nSOLUTION 3: Check Production Logs")
    print("- Go to Render dashboard > your service > Logs")
    print("- Look for authentication errors when you try to login")
    print("- Check for database connection issues")
    
    print("\nSOLUTION 4: Manual Database Check")
    print("- Run this script on Render shell: python create_direct_admin_login.py")
    print("- This will recreate the admin user from scratch")
    
    print("\nSOLUTION 5: Temporary Settings Override")
    print("- If all else fails, we can temporarily disable django-allauth")
    print("- This would require a code change and redeployment")

if __name__ == '__main__':
    test_admin_access()
    check_allauth_interference()
    provide_solutions()