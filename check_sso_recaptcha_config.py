"""
Diagnostic script to check SSO and reCAPTCHA configuration
Run with: python manage.py shell < check_sso_recaptcha_config.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from core.models.sso_config import SSOConfig
from core.models.recaptcha_config import ReCaptchaConfig
from core.sso_utils import get_enabled_sso_providers
from core.recaptcha_utils import is_recaptcha_enabled, get_recaptcha_public_key

print("=" * 80)
print("SSO AND RECAPTCHA CONFIGURATION DIAGNOSTIC")
print("=" * 80)

# Check SSO Configuration
print("\n1. SSO CONFIGURATION")
print("-" * 80)
sso_configs = SSOConfig.objects.all()
print(f"Total SSO configs in database: {sso_configs.count()}")

for config in sso_configs:
    print(f"\n  Config: {config.name}")
    print(f"  Provider: {config.provider}")
    print(f"  Is Active: {config.is_active}")
    print(f"  Enabled: {config.enabled}")
    print(f"  Is Verified: {config.is_verified}")
    print(f"  Client ID: {config.client_id[:20]}..." if config.client_id else "  Client ID: (empty)")
    print(f"  Secret Key: {config.secret_key[:20]}..." if config.secret_key else "  Secret Key: (empty)")
    print(f"  Scopes: {config.scopes}")

print("\n  Active & Enabled SSO Providers:")
active_sso = SSOConfig.objects.filter(is_active=True, enabled=True)
if active_sso.exists():
    for config in active_sso:
        print(f"    ✓ {config.provider} - {config.name}")
else:
    print("    ✗ No active and enabled SSO providers found")

print("\n  get_enabled_sso_providers() returns:")
enabled_providers = get_enabled_sso_providers()
print(f"    {enabled_providers}")

# Check reCAPTCHA Configuration
print("\n2. RECAPTCHA CONFIGURATION")
print("-" * 80)
recaptcha_configs = ReCaptchaConfig.objects.all()
print(f"Total reCAPTCHA configs in database: {recaptcha_configs.count()}")

for config in recaptcha_configs:
    print(f"\n  Config: {config.name}")
    print(f"  Version: {config.version}")
    print(f"  Enabled: {config.enabled}")
    print(f"  Site Key: {config.site_key[:20]}..." if config.site_key else "  Site Key: (empty)")
    print(f"  Secret Key: {config.secret_key[:20]}..." if config.secret_key else "  Secret Key: (empty)")
    print(f"  Threshold: {config.threshold}")

print("\n  Active reCAPTCHA Config:")
active_recaptcha = ReCaptchaConfig.get_active_config()
if active_recaptcha:
    print(f"    ✓ {active_recaptcha.name} (v{active_recaptcha.version})")
    print(f"    Enabled: {active_recaptcha.enabled}")
    print(f"    Site Key: {active_recaptcha.site_key[:20]}..." if active_recaptcha.site_key else "    Site Key: (empty)")
else:
    print("    ✗ No active reCAPTCHA configuration found")

print("\n  is_recaptcha_enabled() returns:")
print(f"    {is_recaptcha_enabled()}")

print("\n  get_recaptcha_public_key() returns:")
public_key = get_recaptcha_public_key()
if public_key:
    print(f"    {public_key[:20]}...")
else:
    print("    (empty)")

# Check Context Processor Output
print("\n3. CONTEXT PROCESSOR OUTPUT")
print("-" * 80)

from django.test import RequestFactory
from core.context_processors import sso_context, recaptcha_context

factory = RequestFactory()
request = factory.get('/')

sso_ctx = sso_context(request)
print("\n  sso_context() returns:")
print(f"    sso_providers: {sso_ctx.get('sso_providers')}")
print(f"    enabled_sso_providers: {sso_ctx.get('enabled_sso_providers')}")

recaptcha_ctx = recaptcha_context(request)
print("\n  recaptcha_context() returns:")
print(f"    recaptcha_enabled: {recaptcha_ctx.get('recaptcha_enabled')}")
print(f"    recaptcha_public_key: {recaptcha_ctx.get('recaptcha_public_key')[:20] if recaptcha_ctx.get('recaptcha_public_key') else '(empty)'}")
print(f"    recaptcha_site_key: {recaptcha_ctx.get('recaptcha_site_key')[:20] if recaptcha_ctx.get('recaptcha_site_key') else '(empty)'}")

# Summary
print("\n4. SUMMARY")
print("-" * 80)

issues = []

if not enabled_providers:
    issues.append("✗ No SSO providers are enabled")
else:
    print(f"✓ SSO providers enabled: {', '.join(enabled_providers)}")

if not is_recaptcha_enabled():
    issues.append("✗ reCAPTCHA is not enabled")
else:
    print("✓ reCAPTCHA is enabled")

if not public_key:
    issues.append("✗ reCAPTCHA public key is missing")
else:
    print("✓ reCAPTCHA public key is configured")

if issues:
    print("\nISSUES FOUND:")
    for issue in issues:
        print(f"  {issue}")
else:
    print("\n✓ All configurations look good!")

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)
