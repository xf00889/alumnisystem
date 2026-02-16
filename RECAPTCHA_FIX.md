# reCAPTCHA Cache Fix for Hosting

## Problem
The hosting server has cached an old reCAPTCHA configuration that's causing login issues even though reCAPTCHA is not configured in the database.

## Root Cause
The `is_recaptcha_enabled()` function was previously falling back to Django settings (which had test keys), causing it to return `True` even without database configuration. This value was cached for 5 minutes, and the hosting server still has the old cached value.

## Immediate Fix Options (Choose One)

### Option 0: Emergency Environment Variable (FASTEST - Immediate Fix)
Add this environment variable to completely bypass reCAPTCHA:

**For Render:**
1. Go to your web service dashboard
2. Click "Environment" tab
3. Add new environment variable:
   - Key: `DISABLE_RECAPTCHA`
   - Value: `True`
4. Click "Save Changes"
5. Application will auto-restart

**For other hosting platforms:**
Add to your `.env` file or environment variables:
```
DISABLE_RECAPTCHA=True
```

Then restart your application.

**Important:** This is an emergency override. Remove it after the cache issue is resolved.

### Option 1: Clear Cache via Management Command (RECOMMENDED)
```bash
python manage.py clear_recaptcha_cache
```

This will:
- Clear the `recaptcha_active_config` cache key
- Clear related cache keys
- Show verification command to confirm the fix

### Option 2: Clear Cache via Django Shell
```bash
python manage.py shell
```
Then run:
```python
from django.core.cache import cache
cache.delete('recaptcha_active_config')
print("✓ Cache cleared!")
exit()
```

### Option 3: Trigger New Deployment
If using Render:
1. Go to your Render dashboard
2. Select your web service
3. Click "Manual Deploy" > "Clear build cache & deploy"
4. Wait for deployment to complete (build script will auto-clear cache)

### Option 4: Restart the Application
If using Render:
1. Go to your Render dashboard
2. Select your web service
3. Click "Manual Deploy" > "Deploy latest commit"
4. Or use the "Restart" button if available

Note: Restarting will clear the in-memory cache if you're using local memory cache, but if you're using Redis, you'll need Option 1 or 2.

## Verify the Fix
After applying any of the above options, verify reCAPTCHA is disabled:

```bash
python manage.py shell -c "from core.recaptcha_utils import is_recaptcha_enabled; print(f'reCAPTCHA enabled: {is_recaptcha_enabled()}')"
```

**Expected output:** `reCAPTCHA enabled: False`

If you see `True`, the cache hasn't been cleared yet. Try Option 1 or 2 again.

## What Was Changed

### 1. core/recaptcha_utils.py
- **Modified `is_recaptcha_enabled()`**: No longer falls back to Django settings
- **Only returns True** when there's a valid database configuration with:
  - `enabled = True`
  - Valid `site_key` and `secret_key`
- **Modified `get_recaptcha_config()`**: Properly caches `False` values to avoid repeated database queries

### 2. accounts/forms.py
- **Made captcha field optional**: `required=False` in both `CustomLoginForm` and `CustomSignupForm`
- **Only adds captcha field** when `is_recaptcha_enabled()` returns `True`

### 3. templates/account/login.html
- **Conditional reCAPTCHA rendering**: Only renders reCAPTCHA widget when `recaptcha_enabled` is `True`
- **Safe JavaScript validation**: Checks if captcha widget exists before validating
- **Graceful fallback**: Allows form submission when reCAPTCHA is not configured

### 4. build.sh
- **Added cache clearing**: `python manage.py clear_recaptcha_cache` runs on every deployment
- **Prevents future issues**: Ensures fresh configuration after each deployment

### 5. New Management Command
- **Created**: `core/management/commands/clear_recaptcha_cache.py`
- **Purpose**: Clears all reCAPTCHA-related cache keys
- **Usage**: `python manage.py clear_recaptcha_cache`

### 6. Emergency Override Environment Variable
- **Added**: `DISABLE_RECAPTCHA` setting in `norsu_alumni/settings.py`
- **Purpose**: Completely bypass reCAPTCHA checks (emergency use only)
- **Usage**: Set `DISABLE_RECAPTCHA=True` in environment variables
- **When to use**: When cache clearing doesn't work or immediate fix is needed

## Cache Behavior

### Cache TTL
- **Duration**: 5 minutes (300 seconds)
- **Key**: `recaptcha_active_config`
- **Caches**: Both `True` (valid config) and `False` (no config)

### Why Cache?
- Avoids database queries on every request
- Improves performance for high-traffic sites
- Safe because config changes are rare

### When Cache is Cleared
1. **Automatic**: On every deployment (via build script)
2. **Manual**: When you run `python manage.py clear_recaptcha_cache`
3. **Expiration**: After 5 minutes (TTL)

## Future Deployments
✓ Cache will be automatically cleared on every deployment  
✓ No manual intervention needed  
✓ This issue won't happen again

## Testing After Fix

### 1. Test Login Without reCAPTCHA
1. Go to login page
2. You should NOT see any reCAPTCHA widget
3. Enter valid credentials
4. Click "Sign In"
5. Should login successfully without any "Security Verification Required" alert

### 2. Test Signup Without reCAPTCHA
1. Go to signup page (click "Sign Up" tab)
2. You should NOT see any reCAPTCHA widget
3. Fill in all required fields
4. Click "Create Account"
5. Should proceed to email verification without any captcha errors

### 3. Verify Configuration
```bash
# Check if reCAPTCHA is enabled
python manage.py shell -c "from core.recaptcha_utils import is_recaptcha_enabled; print(f'Enabled: {is_recaptcha_enabled()}')"

# Check configuration details
python manage.py shell -c "from core.recaptcha_utils import get_recaptcha_config; config = get_recaptcha_config(); print(f'Config: {config}')"
```

Expected outputs:
- `Enabled: False`
- `Config: None`

## Troubleshooting

### Issue: Still seeing "Security Verification Required" alert
**Solution**: Cache hasn't been cleared yet
1. Run: `python manage.py clear_recaptcha_cache`
2. Verify: `python manage.py shell -c "from core.recaptcha_utils import is_recaptcha_enabled; print(is_recaptcha_enabled())"`
3. Should output: `False`

### Issue: reCAPTCHA widget still appears on page
**Solution**: Template cache or browser cache
1. Clear Django cache: `python manage.py clear_recaptcha_cache`
2. Hard refresh browser: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
3. Clear browser cache completely

### Issue: Using Redis and cache won't clear
**Solution**: Clear Redis cache manually
```bash
python manage.py shell
```
```python
from django.core.cache import cache
cache.clear()  # Clears ALL cache (use with caution)
exit()
```

Or clear specific key:
```python
from django.core.cache import cache
cache.delete('recaptcha_active_config')
exit()
```

## Configuring reCAPTCHA (Optional)

If you want to enable reCAPTCHA in the future:

1. **Get reCAPTCHA keys** from Google: https://www.google.com/recaptcha/admin
2. **Add configuration** via Django admin or database:
   - Go to: `/admin/core/recaptchaconfig/`
   - Create new configuration
   - Set `enabled = True`
   - Add your `site_key` and `secret_key`
   - Choose version (v2 or v3)
   - Set threshold (for v3, default: 0.5)
3. **Clear cache**: `python manage.py clear_recaptcha_cache`
4. **Test**: reCAPTCHA should now appear on login/signup pages

## Summary

✓ **Fixed**: reCAPTCHA no longer blocks login when not configured  
✓ **Safe**: Graceful fallback when reCAPTCHA is disabled  
✓ **Automatic**: Cache clears on every deployment  
✓ **Manual**: Can clear cache anytime with management command  
✓ **Future-proof**: Won't have this issue again
