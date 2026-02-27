#!/usr/bin/env python
"""
Test script to verify SSO context is properly passed to login page
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser
from accounts.security_views import custom_login_view
from core.context_processors import sso_context

print("=" * 80)
print("SSO LOGIN CONTEXT TEST")
print("=" * 80)

# Create a mock request
factory = RequestFactory()
request = factory.get('/accounts/login/')
request.user = AnonymousUser()

# Add session and messages middleware attributes
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.messages.storage.fallback import FallbackStorage

middleware = SessionMiddleware(lambda x: None)
middleware.process_request(request)
request.session.save()

# Add messages
setattr(request, '_messages', FallbackStorage(request))

print("\n1. Testing context processor:")
print("-" * 80)
ctx = sso_context(request)
print(f"   sso_providers: {ctx.get('sso_providers')}")
print(f"   enabled_sso_providers: {ctx.get('enabled_sso_providers')}")

print("\n2. Testing custom_login_view:")
print("-" * 80)
try:
    response = custom_login_view(request)
    print(f"   Response status: {response.status_code}")
    print(f"   Response type: {type(response).__name__}")
    
    if hasattr(response, 'context_data'):
        print(f"   Has context_data: Yes")
        print(f"   enabled_sso_providers in context: {response.context_data.get('enabled_sso_providers')}")
        print(f"   recaptcha_enabled in context: {response.context_data.get('recaptcha_enabled')}")
        print(f"   recaptcha_site_key in context: {response.context_data.get('recaptcha_site_key')}")
    else:
        print(f"   Has context_data: No")
        print(f"   Note: Context should be passed via extra_context parameter")
        
except Exception as e:
    print(f"   Error: {e}")
    import traceback
    traceback.print_exc()

print("\n3. Checking SSO configuration:")
print("-" * 80)
from core.models import SSOConfig
enabled_providers = SSOConfig.get_enabled_providers()
print(f"   Enabled providers: {[p.provider_type for p in enabled_providers]}")
print(f"   Count: {len(enabled_providers)}")

for provider in enabled_providers:
    print(f"\n   Provider: {provider.provider_type}")
    print(f"   - Display Name: {provider.display_name}")
    print(f"   - Is Active: {provider.is_active}")
    print(f"   - Enabled: {provider.enabled}")
    print(f"   - Client ID: {provider.client_id[:20]}..." if provider.client_id else "   - Client ID: None")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
