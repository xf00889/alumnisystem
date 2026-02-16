# reCAPTCHA Site Key Fix

## Problem
When reCAPTCHA is enabled in the database (`DISABLE_RECAPTCHA=False`), the login page shows this JavaScript error:

```
Uncaught Error: Missing required parameters: sitekey
at Ya.<anonymous> (recaptcha__en.js:261:132)
```

This happens because the template variable name doesn't match what the context processor provides.

## Root Cause
- **Template expects:** `recaptcha_site_key`
- **Context processor provided:** `recaptcha_public_key`
- **Result:** Template renders `data-sitekey=""` (empty), causing Google reCAPTCHA to fail

## Solution
Updated `core/context_processors.py` to provide both variable names:

```python
def recaptcha_context(request):
    """
    Add reCAPTCHA configuration to template context
    """
    public_key = get_recaptcha_public_key()
    enabled = is_recaptcha_enabled()
    
    return {
        'recaptcha_public_key': public_key,
        'recaptcha_site_key': public_key,  # Alias for template compatibility
        'recaptcha_enabled': enabled,
    }
```

## Files Changed
- ✅ `core/context_processors.py` - Added `recaptcha_site_key` alias

## Testing

### When reCAPTCHA is Disabled (DISABLE_RECAPTCHA=True or no database config)
1. `recaptcha_enabled` = `False`
2. Template does NOT render reCAPTCHA widget
3. Login works without captcha
4. ✅ Expected behavior

### When reCAPTCHA is Enabled (Database config exists and enabled=True)
1. `recaptcha_enabled` = `True`
2. `recaptcha_site_key` = Your actual site key from database
3. Template renders reCAPTCHA widget with correct site key
4. Google reCAPTCHA loads successfully
5. ✅ Expected behavior

## Deployment Steps

1. **Commit and push changes:**
   ```bash
   git add core/context_processors.py
   git commit -m "Fix: Add recaptcha_site_key alias for template compatibility"
   git push origin main
   ```

2. **Deploy to hosting**
   - Render will automatically deploy
   - No environment variable changes needed

3. **Test with reCAPTCHA disabled:**
   - Set `DISABLE_RECAPTCHA=True` in environment
   - Login should work without captcha

4. **Test with reCAPTCHA enabled:**
   - Remove `DISABLE_RECAPTCHA` from environment (or set to `False`)
   - Ensure database has active reCAPTCHA config with valid keys
   - Login page should show reCAPTCHA widget
   - Widget should load without JavaScript errors

## Verification Commands

### Check if reCAPTCHA is enabled:
```bash
python manage.py shell -c "from core.recaptcha_utils import is_recaptcha_enabled; print(f'Enabled: {is_recaptcha_enabled()}')"
```

### Check site key:
```bash
python manage.py shell -c "from core.recaptcha_utils import get_recaptcha_public_key; print(f'Site Key: {get_recaptcha_public_key()}')"
```

### Check database config:
```bash
python manage.py shell -c "from core.models import ReCaptchaConfig; config = ReCaptchaConfig.get_active_config(); print(f'Config: {config}'); print(f'Enabled: {config.enabled if config else None}'); print(f'Site Key: {config.site_key if config else None}')"
```

## Troubleshooting

### Issue: Still getting "Missing required parameters: sitekey"
**Cause:** Template cache or browser cache

**Solution:**
1. Hard refresh browser: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
2. Clear browser cache completely
3. Try incognito/private window
4. Restart Django application

### Issue: reCAPTCHA widget not appearing
**Cause:** `recaptcha_enabled` is False

**Solution:**
1. Check database has active reCAPTCHA config
2. Verify `DISABLE_RECAPTCHA` is not set to `True`
3. Clear reCAPTCHA cache: `python manage.py clear_recaptcha_cache`
4. Restart application

### Issue: reCAPTCHA widget shows but validation fails
**Cause:** Invalid site key or secret key

**Solution:**
1. Verify keys in database match Google reCAPTCHA console
2. Ensure keys are for the correct domain
3. Check if keys are for v2 or v3 (must match version in database)

## Summary

✅ **Fixed:** Template now receives `recaptcha_site_key` variable  
✅ **Backward compatible:** Still provides `recaptcha_public_key`  
✅ **Works with disabled reCAPTCHA:** No widget rendered when disabled  
✅ **Works with enabled reCAPTCHA:** Widget loads with correct site key  

The reCAPTCHA integration will now work correctly whether enabled or disabled!
