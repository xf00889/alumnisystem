#!/usr/bin/env python
"""
Test script to check what messages are generated on failed login
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage

User = get_user_model()

print("=" * 80)
print("LOGIN MESSAGES TEST")
print("=" * 80)

# Create a test client
client = Client()

# Try to login with incorrect credentials
print("\n1. Testing login with incorrect password:")
print("-" * 80)
response = client.post('/accounts/login/', {
    'login': 'test@example.com',
    'password': 'wrongpassword'
}, follow=True)

print(f"Response status: {response.status_code}")
print(f"Response URL: {response.request['PATH_INFO']}")

# Get messages from the response
messages = list(get_messages(response.wsgi_request))
print(f"\nMessages count: {len(messages)}")

for i, message in enumerate(messages, 1):
    print(f"\nMessage {i}:")
    print(f"  Level: {message.level_tag}")
    print(f"  Tags: {message.tags}")
    print(f"  Text: {message.message}")
    print(f"  Text (lowercase): {message.message.lower()}")
    
    # Check if message would be filtered
    message_text = message.message.lower()
    filtered = ('signed out' in message_text or 'logged out' in message_text or 
                'sign out' in message_text or 'log out' in message_text or 
                'logout' in message_text or 'signed in' in message_text or 
                'logged in' in message_text or 'google sign-in' in message_text or 
                'cancelled' in message_text or 'access_denied' in message_text or
                'successfully signed in' in message_text)
    
    print(f"  Would be filtered: {filtered}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
