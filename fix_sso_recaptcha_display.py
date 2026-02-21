"""
Script to verify and fix SSO and reCAPTCHA display issues
Run with: python manage.py shell < fix_sso_recaptcha_display.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from core.models.sso_config import SSOConfig
from core.models.recaptcha_config import ReCaptchaConfig
from core.sso_utils import clear_sso_cache
from core.recaptcha_utils import clear_recaptcha_cache

print("=" * 80)
print("SSO AND RECAPTCHA DISPLAY FIX")
print("=" * 80)

# Step 1: Clear caches
print("\n1. Clearing caches...")
clear_sso_cache()
clear_recaptcha_cache()
print("   ✓ Caches cleared")

# Step 2: Check SSO Configuration
print("\n2. Checking SSO Configuration...")
active_sso = SSOConfig.objects.filter(is_active=True, enabled=True)

if not active_sso.exists():
    print("   ✗ No active and enabled SSO configurations found")
    print("\n   Available SSO configurations:")
    all_sso = SSOConfig.objects.all()
    if all_sso.exists():
        for config in all_sso:
            print(f"     - {config.name} (Provider: {config.provider})")
            print(f"       is_active: {config.is_active}, enabled: {config.enabled}")
        
        print("\n   To fix: Set is_active=True and enabled=True for your SSO config")
        print("   You can do this in Django admin or run:")
        print("   >>> from core.models.sso_config import SSOConfig")
        print("   >>> config = SSOConfig.objects.get(id=YOUR_CONFIG_ID)")
        print("   >>> config.is_active = True")
        print("   >>> config.enabled = True")
        print("   >>> config.save()")
    else:
        print("     No SSO configurations found in database")
        print("     Create one in Django admin at: /admin/core/ssoconfig/")
else:
    for config in active_sso:
        print(f"   ✓ Active SSO: {config.provider} - {config.name}")
        if not config.client_id or len(config.client_id) < 10:
            print(f"     ⚠ Warning: Client ID looks invalid")
        if not config.secret_key or len(config.secret_key) < 10:
            print(f"     ⚠ Warning: Secret Key looks invalid")

# Step 3: Check reCAPTCHA Configuration
print("\n3. Checking reCAPTCHA Configuration...")
active_recaptcha = ReCaptchaConfig.get_active_config()

if not active_recaptcha:
    print("   ✗ No active reCAPTCHA configuration found")
    print("\n   Available reCAPTCHA configurations:")
    all_recaptcha = ReCaptchaConfig.objects.all()
    if all_recaptcha.exists():
        for config in all_recaptcha:
            print(f"     - {config.name} (Version: {config.version})")
            print(f"       enabled: {config.enabled}")
        
        print("\n   To fix: Set enabled=True for your reCAPTCHA config")
        print("   You can do this in Django admin or run:")
        print("   >>> from core.models.recaptcha_config import ReCaptchaConfig")
        print("   >>> config = ReCaptchaConfig.objects.get(id=YOUR_CONFIG_ID)")
        print("   >>> config.enabled = True")
        print("   >>> config.save()")
    else:
        print("     No reCAPTCHA configurations found in database")
        print("     Create one in Django admin at: /admin/core/recaptchaconfig/")
elif not active_recaptcha.enabled:
    print(f"   ✗ reCAPTCHA config exists but is disabled: {active_recaptcha.name}")
    print("   To fix: Set enabled=True")
else:
    print(f"   ✓ Active reCAPTCHA: {active_recaptcha.name} (v{active_recaptcha.version})")
    if not active_recaptcha.site_key or len(active_recaptcha.site_key) < 10:
        print(f"     ⚠ Warning: Site Key looks invalid")
    if not active_recaptcha.secret_key or len(active_recaptcha.secret_key) < 10:
        print(f"     ⚠ Warning: Secret Key looks invalid")

# Step 4: Test context processors
print("\n4. Testing context processors...")
from django.test import RequestFactory
from core.context_processors import sso_context, recaptcha_context

factory = RequestFactory()
request = factory.get('/')

sso_ctx = sso_context(request)
recaptcha_ctx = recaptcha_context(request)

print(f"   enabled_sso_providers: {sso_ctx.get('enabled_sso_providers')}")
print(f"   recaptcha_enabled: {recaptcha_ctx.get('recaptcha_enabled')}")
print(f"   recaptcha_site_key: {'(set)' if recaptcha_ctx.get('recaptcha_site_key') else '(empty)'}")

# Step 5: Recommendations
print("\n5. RECOMMENDATIONS")
print("-" * 80)

if not active_sso.exists():
    print("   1. Enable your SSO configuration:")
    print("      - Go to Django admin: /admin/core/ssoconfig/")
    print("      - Find your Google OAuth config")
    print("      - Check 'Is active' and 'Enabled' boxes")
    print("      - Save")

if not active_recaptcha or not active_recaptcha.enabled:
    print("   2. Enable your reCAPTCHA configuration:")
    print("      - Go to Django admin: /admin/core/recaptchaconfig/")
    print("      - Find your reCAPTCHA config")
    print("      - Check 'Enabled' box")
    print("      - Save")

print("\n   3. After making changes:")
print("      - Clear browser cache")
print("      - Restart your Django server")
print("      - Visit the login page: /accounts/login/")

print("\n" + "=" * 80)
print("FIX SCRIPT COMPLETE")
print("=" * 80)
