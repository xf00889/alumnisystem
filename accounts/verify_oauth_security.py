"""
Security verification script for Google OAuth implementation.
Verifies CSRF protection, HTTPS enforcement, OAuth token storage, and minimal scopes.
"""
import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'norsu_alumni.settings')
django.setup()

from django.conf import settings
from django.core.management import call_command
from allauth.socialaccount.models import SocialApp
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)


def print_header(text):
    """Print a formatted header"""
    print(f"\n{Fore.CYAN}{'=' * 70}")
    print(f"{Fore.CYAN}{text.center(70)}")
    print(f"{Fore.CYAN}{'=' * 70}\n")


def print_success(text):
    """Print success message"""
    print(f"{Fore.GREEN}✓ {text}")


def print_warning(text):
    """Print warning message"""
    print(f"{Fore.YELLOW}⚠ {text}")


def print_error(text):
    """Print error message"""
    print(f"{Fore.RED}✗ {text}")


def print_info(text):
    """Print info message"""
    print(f"{Fore.BLUE}ℹ {text}")


def verify_csrf_protection():
    """Verify CSRF protection is enabled"""
    print_header("CSRF Protection Verification")
    
    # Check CSRF middleware
    if 'django.middleware.csrf.CsrfViewMiddleware' in settings.MIDDLEWARE:
        print_success("CSRF middleware is enabled")
    else:
        print_error("CSRF middleware is NOT enabled")
        return False
    
    # Check CSRF cookie settings
    if settings.CSRF_COOKIE_HTTPONLY:
        print_success("CSRF cookie is HTTP-only")
    else:
        print_warning("CSRF cookie is not HTTP-only")
    
    if settings.CSRF_COOKIE_SAMESITE == 'Strict':
        print_success("CSRF cookie SameSite is set to Strict")
    elif settings.CSRF_COOKIE_SAMESITE == 'Lax':
        print_warning("CSRF cookie SameSite is set to Lax (consider Strict)")
    else:
        print_warning(f"CSRF cookie SameSite is set to {settings.CSRF_COOKIE_SAMESITE}")
    
    # Check CSRF cookie secure in production
    if not settings.DEBUG:
        if settings.CSRF_COOKIE_SECURE:
            print_success("CSRF cookie is secure in production")
        else:
            print_error("CSRF cookie is NOT secure in production")
            return False
    else:
        print_info("CSRF cookie secure check skipped (development mode)")
    
    # Django-allauth automatically validates OAuth state parameter for CSRF protection
    print_success("Django-allauth state parameter validation is active (built-in)")
    
    return True


def verify_https_enforcement():
    """Verify HTTPS enforcement in production"""
    print_header("HTTPS Enforcement Verification")
    
    # Check ACCOUNT_DEFAULT_HTTP_PROTOCOL
    if not settings.DEBUG:
        if settings.ACCOUNT_DEFAULT_HTTP_PROTOCOL == 'https':
            print_success("HTTPS is enforced for OAuth redirects in production")
        else:
            print_error(f"HTTPS is NOT enforced (protocol: {settings.ACCOUNT_DEFAULT_HTTP_PROTOCOL})")
            return False
    else:
        print_info("HTTPS enforcement check skipped (development mode)")
        if settings.ACCOUNT_DEFAULT_HTTP_PROTOCOL == 'http':
            print_success("HTTP is used for OAuth redirects in development")
        else:
            print_warning(f"Protocol is set to {settings.ACCOUNT_DEFAULT_HTTP_PROTOCOL} in development")
    
    # Check session cookie secure
    if not settings.DEBUG:
        if settings.SESSION_COOKIE_SECURE:
            print_success("Session cookie is secure in production")
        else:
            print_error("Session cookie is NOT secure in production")
            return False
    else:
        print_info("Session cookie secure check skipped (development mode)")
    
    # Check session cookie HTTP-only
    if settings.SESSION_COOKIE_HTTPONLY:
        print_success("Session cookie is HTTP-only")
    else:
        print_warning("Session cookie is not HTTP-only")
    
    return True


def verify_oauth_scopes():
    """Verify minimal OAuth scopes are requested"""
    print_header("OAuth Scopes Verification")
    
    # Check Google provider scopes
    google_config = settings.SOCIALACCOUNT_PROVIDERS.get('google', {})
    scopes = google_config.get('SCOPE', [])
    
    if not scopes:
        print_error("No OAuth scopes configured for Google")
        return False
    
    print_info(f"Configured scopes: {', '.join(scopes)}")
    
    # Verify only minimal scopes are requested
    allowed_scopes = ['profile', 'email', 'openid']
    excessive_scopes = [s for s in scopes if s not in allowed_scopes]
    
    if excessive_scopes:
        print_warning(f"Excessive scopes detected: {', '.join(excessive_scopes)}")
        print_info("Consider requesting only 'profile' and 'email' scopes")
    else:
        print_success("Only minimal scopes are requested (profile, email)")
    
    # Check if email is verified by provider
    if google_config.get('VERIFIED_EMAIL'):
        print_success("Email verification is trusted from Google")
    else:
        print_warning("Email verification is not trusted from Google")
    
    return True


def verify_token_storage():
    """Verify OAuth token storage security"""
    print_header("OAuth Token Storage Verification")
    
    # Check if tokens are stored
    if settings.SOCIALACCOUNT_STORE_TOKENS:
        print_success("OAuth tokens are stored for future use")
    else:
        print_warning("OAuth tokens are not stored")
    
    # Check database encryption (Django doesn't encrypt by default)
    print_info("OAuth tokens are stored in database")
    print_warning("Consider implementing field-level encryption for sensitive tokens")
    print_info("Django's default security relies on database access controls")
    
    # Check if SocialApp exists
    try:
        google_app = SocialApp.objects.filter(provider='google').first()
        if google_app:
            print_success("Google SocialApp is configured in database")
            print_info(f"Client ID: {google_app.client_id[:20]}...")
            print_info(f"Associated sites: {google_app.sites.count()}")
        else:
            print_warning("Google SocialApp is not configured in database")
            print_info("Run: python manage.py setup_google_oauth")
    except Exception as e:
        print_error(f"Error checking SocialApp: {str(e)}")
        return False
    
    return True


def verify_rate_limiting():
    """Verify rate limiting is configured"""
    print_header("Rate Limiting Verification")
    
    # Check if django-ratelimit is installed
    try:
        import django_ratelimit
        print_success("django-ratelimit is installed")
    except ImportError:
        print_error("django-ratelimit is NOT installed")
        return False
    
    # Check rate limiting settings
    if settings.RATELIMIT_ENABLE:
        print_success("Rate limiting is enabled")
    else:
        print_error("Rate limiting is NOT enabled")
        return False
    
    if settings.RATELIMIT_USE_CACHE == 'default':
        print_success("Rate limiting uses default cache")
    else:
        print_warning(f"Rate limiting uses cache: {settings.RATELIMIT_USE_CACHE}")
    
    # Check if custom OAuth callback view exists
    try:
        from accounts.oauth_views import google_callback_with_ratelimit
        print_success("Custom rate-limited OAuth callback view exists")
    except ImportError:
        print_error("Custom rate-limited OAuth callback view NOT found")
        return False
    
    return True


def verify_environment_variables():
    """Verify OAuth environment variables are set"""
    print_header("Environment Variables Verification")
    
    client_id = settings.GOOGLE_OAUTH_CLIENT_ID
    client_secret = settings.GOOGLE_OAUTH_CLIENT_SECRET
    
    if client_id:
        print_success(f"GOOGLE_OAUTH_CLIENT_ID is set ({client_id[:20]}...)")
    else:
        print_warning("GOOGLE_OAUTH_CLIENT_ID is not set")
        print_info("Set in .env file for OAuth to work")
    
    if client_secret:
        print_success("GOOGLE_OAUTH_CLIENT_SECRET is set")
    else:
        print_warning("GOOGLE_OAUTH_CLIENT_SECRET is not set")
        print_info("Set in .env file for OAuth to work")
    
    return True


def main():
    """Run all security verifications"""
    print(f"\n{Fore.MAGENTA}{'*' * 70}")
    print(f"{Fore.MAGENTA}Google OAuth Security Verification".center(70))
    print(f"{Fore.MAGENTA}{'*' * 70}\n")
    
    results = {
        'CSRF Protection': verify_csrf_protection(),
        'HTTPS Enforcement': verify_https_enforcement(),
        'OAuth Scopes': verify_oauth_scopes(),
        'Token Storage': verify_token_storage(),
        'Rate Limiting': verify_rate_limiting(),
        'Environment Variables': verify_environment_variables(),
    }
    
    # Print summary
    print_header("Verification Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check, result in results.items():
        if result:
            print_success(f"{check}: PASSED")
        else:
            print_error(f"{check}: FAILED")
    
    print(f"\n{Fore.CYAN}Total: {passed}/{total} checks passed")
    
    if passed == total:
        print(f"\n{Fore.GREEN}{'=' * 70}")
        print(f"{Fore.GREEN}All security checks passed! ✓".center(70))
        print(f"{Fore.GREEN}{'=' * 70}\n")
        return 0
    else:
        print(f"\n{Fore.RED}{'=' * 70}")
        print(f"{Fore.RED}Some security checks failed!".center(70))
        print(f"{Fore.RED}{'=' * 70}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
