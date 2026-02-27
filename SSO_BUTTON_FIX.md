# SSO Button Missing Fix

## Issue Description
The Google Sign-In button disappeared from the login page after implementing password validation.

## Root Cause
The `custom_login_view` in `accounts/security_views.py` was using an incorrect method name to get SSO providers:
- Used: `SSOConfig.get_enabled_providers()` ❌
- Correct: Query `SSOConfig.objects.filter(is_active=True, enabled=True)` ✓

Additionally, the context was not being passed correctly to the allauth LoginView.

## Solution Implemented

### 1. Fixed Method Call (accounts/security_views.py)

**Before:**
```python
try:
    from core.models import SSOConfig
    enabled_providers = SSOConfig.get_enabled_providers()  # ❌ Method doesn't exist
    context['enabled_sso_providers'] = [p.provider_type for p in enabled_providers]
except Exception as e:
    logger.error(f"Error getting SSO providers: {e}")
    context['enabled_sso_providers'] = []
```

**After:**
```python
try:
    from core.models import SSOConfig
    enabled_providers = SSOConfig.objects.filter(is_active=True, enabled=True)  # ✓ Direct query
    context['enabled_sso_providers'] = [p.provider for p in enabled_providers]  # ✓ Use 'provider' field
except Exception as e:
    logger.error(f"Error getting SSO providers: {e}")
    context['enabled_sso_providers'] = []
```

### 2. Fixed Context Passing

**Before:**
```python
view = LoginView.as_view()
response = view(request)

# If it's a render response, add our context
if hasattr(response, 'context_data'):
    response.context_data.update(context)  # ❌ Doesn't work reliably

return response
```

**After:**
```python
view = LoginView.as_view(extra_context=context)  # ✓ Pass context directly
response = view(request)

return response
```

## Verification

### Test Results
```
SSO LOGIN CONTEXT TEST
================================================================================

1. Testing context processor:
--------------------------------------------------------------------------------
   sso_providers: ['google']
   enabled_sso_providers: ['google']

2. Testing custom_login_view:
--------------------------------------------------------------------------------
   Response status: 200
   Response type: TemplateResponse
   Has context_data: Yes
   enabled_sso_providers in context: ['google']  ✓
   recaptcha_enabled in context: False
   recaptcha_site_key in context: 6Le7kesrAAAAAAyjoHeSENUJf9MpmKUdrT7JjbOg
```

### Template Check
The login template checks for SSO providers:
```django
{% if 'google' in enabled_sso_providers %}
    <div class="divider">
        <div class="divider-line"></div>
        <span class="divider-text">or</span>
        <div class="divider-line"></div>
    </div>

    <a href="/accounts/google/login/" class="btn-google">
        <svg>...</svg>
        Continue with Google
    </a>
{% endif %}
```

With `enabled_sso_providers = ['google']`, the condition is now `True` ✓

## Key Learnings

### 1. SSOConfig Model Methods
- `get_active_providers()` - Returns a dictionary for django-allauth configuration
- Direct query needed for template context: `SSOConfig.objects.filter(is_active=True, enabled=True)`

### 2. Class-Based View Context
- Use `extra_context` parameter when calling `as_view()`
- Don't try to modify `context_data` after the response is created
- Context processors run automatically and don't need manual addition

### 3. Field Names
- SSOConfig model uses `provider` field, not `provider_type`
- Always check model definitions when accessing fields

## Related Files Modified
- `accounts/security_views.py` - Fixed SSO provider query and context passing

## Related Files (No Changes)
- `templates/account/login.html` - Template logic is correct
- `core/context_processors.py` - Context processor works correctly
- `core/models/sso_config.py` - Model is correct

## Testing Checklist
- [x] SSO button appears on login page
- [x] SSO button appears on signup tab
- [x] Context processor provides correct data
- [x] Custom login view passes context correctly
- [x] No errors in console
- [x] Google OAuth flow works

## CSP Warnings (Not an Issue)
The Content-Security-Policy warnings about reCAPTCHA are normal and expected:
```
Partitioned cookie or storage access was provided to "https://www.google.com/recaptcha/..."
```

These warnings occur because:
1. reCAPTCHA is a third-party service
2. Modern browsers partition cookies for privacy
3. The warnings don't affect functionality
4. They can be safely ignored

## Deployment Notes
- No database migrations required
- No settings changes required
- Backend code change only (security_views.py)
- Safe to deploy without downtime
- Backward compatible

## Future Improvements
1. Add unit tests for custom_login_view context
2. Add integration tests for SSO button visibility
3. Consider caching SSO provider list
4. Add admin UI to enable/disable SSO providers
5. Add SSO provider status indicator in admin
