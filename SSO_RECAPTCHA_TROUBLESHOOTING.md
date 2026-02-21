# SSO and reCAPTCHA Display Troubleshooting Guide

## Problem
SSO button and reCAPTCHA indicator are not displaying on the login page, even though they are configured in the hosting database and marked as active.

## Root Cause Analysis

The issue was caused by a mismatch between the context processor variable name and the template variable name:

1. **Context Processor** (`core/context_processors.py`): Was returning `sso_providers`
2. **Login Template** (`templates/account/login.html`): Was checking for `enabled_sso_providers`

This mismatch caused the template condition `{% if 'google' in enabled_sso_providers %}` to always evaluate to False, hiding the SSO button.

## Fix Applied

Updated `core/context_processors.py` to provide both variable names for compatibility:

```python
def sso_context(request):
    """
    Add SSO configuration to template context
    """
    try:
        from core.sso_utils import get_enabled_sso_providers
        enabled_providers = get_enabled_sso_providers()
        return {
            'sso_providers': enabled_providers,
            'enabled_sso_providers': enabled_providers,  # Alias for template compatibility
        }
    except Exception:
        return {
            'sso_providers': [],
            'enabled_sso_providers': [],
        }
```

## Verification Steps

### 1. Run Diagnostic Script

```bash
python manage.py shell < check_sso_recaptcha_config.py
```

This will show:
- All SSO configurations in database
- All reCAPTCHA configurations in database
- Which ones are active and enabled
- What the context processors are returning

### 2. Run Fix Script

```bash
python manage.py shell < fix_sso_recaptcha_display.py
```

This will:
- Clear caches
- Check configurations
- Provide specific recommendations

### 3. Verify Database Configuration

#### Check SSO Configuration:

```python
from core.models.sso_config import SSOConfig

# List all SSO configs
for config in SSOConfig.objects.all():
    print(f"{config.name}: is_active={config.is_active}, enabled={config.enabled}")

# Get active configs
active = SSOConfig.objects.filter(is_active=True, enabled=True)
print(f"Active SSO providers: {[c.provider for c in active]}")
```

#### Check reCAPTCHA Configuration:

```python
from core.models.recaptcha_config import ReCaptchaConfig

# List all reCAPTCHA configs
for config in ReCaptchaConfig.objects.all():
    print(f"{config.name}: enabled={config.enabled}")

# Get active config
active = ReCaptchaConfig.get_active_config()
if active:
    print(f"Active reCAPTCHA: {active.name}, enabled={active.enabled}")
```

### 4. Manual Database Check

If the scripts don't work, check directly in Django admin:

1. **SSO Configuration**: `/admin/core/ssoconfig/`
   - Verify `is_active` = True
   - Verify `enabled` = True
   - Verify `client_id` and `secret_key` are filled

2. **reCAPTCHA Configuration**: `/admin/core/recaptchaconfig/`
   - Verify `enabled` = True
   - Verify `site_key` and `secret_key` are filled

## Common Issues and Solutions

### Issue 1: SSO Button Not Showing

**Symptoms:**
- No "Continue with Google" button on login page
- Template condition `{% if 'google' in enabled_sso_providers %}` evaluates to False

**Solutions:**

1. **Check Database Configuration:**
   ```python
   from core.models.sso_config import SSOConfig
   config = SSOConfig.objects.filter(provider='google').first()
   if config:
       config.is_active = True
       config.enabled = True
       config.save()
   ```

2. **Clear Cache:**
   ```python
   from core.sso_utils import clear_sso_cache
   clear_sso_cache()
   ```

3. **Verify Context Processor:**
   - Check that `core.context_processors.sso_context` is in `TEMPLATES` settings
   - Restart Django server after changes

### Issue 2: reCAPTCHA Badge Not Showing

**Symptoms:**
- No reCAPTCHA badge in bottom-right corner
- reCAPTCHA script not loading

**Solutions:**

1. **Check Database Configuration:**
   ```python
   from core.models.recaptcha_config import ReCaptchaConfig
   config = ReCaptchaConfig.objects.first()
   if config:
       config.enabled = True
       config.save()
   ```

2. **Clear Cache:**
   ```python
   from core.recaptcha_utils import clear_recaptcha_cache
   clear_recaptcha_cache()
   ```

3. **Check Template Variables:**
   - Template checks: `{% if recaptcha_enabled %}`
   - Context processor provides: `recaptcha_enabled`, `recaptcha_site_key`

### Issue 3: Configuration Exists but Not Active

**Symptoms:**
- Configuration visible in admin
- Marked as active/enabled
- Still not showing on login page

**Solutions:**

1. **Restart Django Server:**
   ```bash
   # Stop the server (Ctrl+C)
   # Start again
   python manage.py runserver
   ```

2. **Clear All Caches:**
   ```python
   from django.core.cache import cache
   cache.clear()
   ```

3. **Check for Multiple Configurations:**
   - Only ONE SSO config per provider can be active
   - Only ONE reCAPTCHA config can be active
   - Django enforces this with `unique_together` constraint

### Issue 4: Browser Caching

**Symptoms:**
- Changes made but not visible
- Old version of page still loading

**Solutions:**

1. **Hard Refresh:**
   - Chrome/Firefox: Ctrl + Shift + R (Windows) or Cmd + Shift + R (Mac)
   - Clear browser cache completely

2. **Incognito/Private Mode:**
   - Test in incognito window to bypass cache

3. **Check Browser Console:**
   - Open Developer Tools (F12)
   - Look for JavaScript errors
   - Check if reCAPTCHA script is loading

## Testing After Fix

### 1. Test SSO Button

1. Navigate to `/accounts/login/`
2. Look for "Continue with Google" button
3. Button should appear below the login form
4. Click button to test OAuth flow

### 2. Test reCAPTCHA

1. Navigate to `/accounts/login/`
2. Look for reCAPTCHA badge in bottom-right corner
3. Submit login form
4. Check browser console for reCAPTCHA token generation

### 3. Test Context Variables

Create a test view to inspect context:

```python
from django.shortcuts import render
from core.context_processors import sso_context, recaptcha_context

def test_context(request):
    sso = sso_context(request)
    recaptcha = recaptcha_context(request)
    
    return render(request, 'test_context.html', {
        'sso': sso,
        'recaptcha': recaptcha,
    })
```

Template (`test_context.html`):
```html
<h1>Context Test</h1>
<h2>SSO Context:</h2>
<pre>{{ sso }}</pre>

<h2>reCAPTCHA Context:</h2>
<pre>{{ recaptcha }}</pre>

<h2>Template Variables:</h2>
<p>enabled_sso_providers: {{ enabled_sso_providers }}</p>
<p>recaptcha_enabled: {{ recaptcha_enabled }}</p>
<p>recaptcha_site_key: {{ recaptcha_site_key }}</p>
```

## Production Deployment Checklist

Before deploying to production:

- [ ] SSO configuration is active and enabled
- [ ] reCAPTCHA configuration is enabled
- [ ] Client ID and Secret Key are correct
- [ ] Site Key and Secret Key are correct
- [ ] Context processors are configured in settings
- [ ] Caches are cleared
- [ ] Server is restarted
- [ ] Login page tested in multiple browsers
- [ ] OAuth flow tested end-to-end
- [ ] reCAPTCHA validation tested

## Additional Resources

- **Django Admin:**
  - SSO Config: `/admin/core/ssoconfig/`
  - reCAPTCHA Config: `/admin/core/recaptchaconfig/`

- **Test Pages:**
  - Login: `/accounts/login/`
  - reCAPTCHA Test: `/test-recaptcha/` (if available)

- **Logs:**
  - Check `logs/alumni_system.log` for errors
  - Check browser console for JavaScript errors

## Support

If issues persist after following this guide:

1. Run both diagnostic scripts and save output
2. Check Django logs for errors
3. Verify database has correct configuration
4. Test in incognito mode to rule out caching
5. Check that all migrations are applied: `python manage.py migrate`

## Summary

The fix ensures that the login template receives the correct context variable (`enabled_sso_providers`) from the context processor. After applying the fix:

1. Clear caches (Django and browser)
2. Restart Django server
3. Test login page
4. Verify SSO button and reCAPTCHA badge appear

The SSO button and reCAPTCHA indicator should now display correctly when their respective configurations are active and enabled in the database.
