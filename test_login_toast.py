"""
Test script to verify login toast notifications are working
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages

User = get_user_model()

def test_login_messages():
    """Test that login failures generate proper messages"""
    client = Client()
    
    # Test 1: Login with non-existent user
    print("\n=== Test 1: Login with non-existent user ===")
    response = client.post('/accounts/login/', {
        'login': 'nonexistent@example.com',
        'password': 'wrongpassword'
    })
    
    messages = list(get_messages(response.wsgi_request))
    print(f"Status Code: {response.status_code}")
    print(f"Messages: {[str(m) for m in messages]}")
    print(f"Message Tags: {[m.tags for m in messages]}")
    
    # Test 2: Login with existing user but wrong password
    print("\n=== Test 2: Login with existing user but wrong password ===")
    
    # Create a test user
    try:
        user = User.objects.get(email='test@example.com')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='correctpassword123',
            first_name='Test',
            last_name='User'
        )
        user.is_active = True
        user.save()
        print(f"Created test user: {user.email}")
    
    # Try to login with wrong password
    response = client.post('/accounts/login/', {
        'login': 'test@example.com',
        'password': 'wrongpassword'
    })
    
    messages = list(get_messages(response.wsgi_request))
    print(f"Status Code: {response.status_code}")
    print(f"Messages: {[str(m) for m in messages]}")
    print(f"Message Tags: {[m.tags for m in messages]}")
    
    # Test 3: Multiple failed attempts
    print("\n=== Test 3: Multiple failed login attempts ===")
    for i in range(4):
        response = client.post('/accounts/login/', {
            'login': 'test@example.com',
            'password': 'wrongpassword'
        })
        messages = list(get_messages(response.wsgi_request))
        print(f"Attempt {i+1}: {[str(m) for m in messages]}")
    
    print("\n=== Test Complete ===")

if __name__ == '__main__':
    test_login_messages()
