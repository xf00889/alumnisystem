# Quick Fix for Hosting - reCAPTCHA Issue

## The Problem
Login is blocked with "Security Verification Required" alert even though reCAPTCHA is not configured.

## The Solution (Choose ONE - ordered by speed)

### ⚡ FASTEST: Emergency Environment Variable (Immediate Fix)
Add this to your environment variables in Render:
```
DISABLE_RECAPTCHA=True
```

Then restart your application. This completely bypasses reCAPTCHA checks.

**Steps for Render:**
1. Go to your web service dashboard
2. Click "Environment" tab
3. Add new environment variable:
   - Key: `DISABLE_RECAPTCHA`
   - Value: `True`
4. Click "Save Changes"
5. Application will auto-restart

### 🔄 FAST: Clear Cache Command
SSH into your hosting server or use the console:
```bash
python manage.py clear_recaptcha_cache
```

### 🛠️ ALTERNATIVE: Restart Application
In your Render dashboard:
1. Go to your web service
2. Click "Manual Deploy" > "Deploy latest commit"
3. Wait for deployment to complete (build script will clear cache)

### 🔧 MANUAL: Clear Cache via Shell
```bash
python manage.py shell -c "from django.core.cache import cache; cache.delete('recaptcha_active_config'); print('✓ Cache cleared!')"
```

## Verify It Worked
```bash
python manage.py shell -c "from core.recaptcha_utils import is_recaptcha_enabled; print(f'reCAPTCHA enabled: {is_recaptcha_enabled()}')"
```

**Expected output:** `reCAPTCHA enabled: False`

If you see `True`, try the fix again or use the emergency environment variable.

## Test Login
1. Go to your login page
2. You should NOT see any reCAPTCHA widget
3. Enter credentials and click "Sign In"
4. Should login successfully without any alerts

## Why This Happened
- The hosting server cached an old configuration (5-minute cache)
- The code was fixed to not use fallback settings
- But the old cached value is still in memory
- Clearing the cache or restarting fixes it immediately

## Remove Emergency Override (After Fix)
Once the cache issue is resolved, you can remove the `DISABLE_RECAPTCHA` environment variable:
1. Go to Environment tab in Render
2. Delete the `DISABLE_RECAPTCHA` variable
3. Save changes

The system will now use the database configuration (which is currently disabled).

## Future Deployments
✓ This won't happen again - the build script now auto-clears cache on every deployment

---

**Need help?** See `RECAPTCHA_FIX.md` for detailed troubleshooting.
