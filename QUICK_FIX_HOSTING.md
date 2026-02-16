# Quick Fix for Hosting - reCAPTCHA Issue

## The Problem
Login is blocked with "Security Verification Required" alert even though reCAPTCHA is not configured.

## The Solution (Run ONE of these on your hosting server)

### ⚡ FASTEST: Clear Cache Command
```bash
python manage.py clear_recaptcha_cache
```

### 🔄 ALTERNATIVE: Restart Application
In your Render dashboard:
1. Go to your web service
2. Click "Manual Deploy" > "Deploy latest commit"
3. Wait for deployment to complete

### 🛠️ MANUAL: Clear Cache via Shell
```bash
python manage.py shell -c "from django.core.cache import cache; cache.delete('recaptcha_active_config'); print('✓ Cache cleared!')"
```

## Verify It Worked
```bash
python manage.py shell -c "from core.recaptcha_utils import is_recaptcha_enabled; print(f'reCAPTCHA enabled: {is_recaptcha_enabled()}')"
```

**Expected output:** `reCAPTCHA enabled: False`

If you see `True`, try the fix again or restart your application.

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

## Future Deployments
✓ This won't happen again - the build script now auto-clears cache on every deployment

---

**Need help?** See `RECAPTCHA_FIX.md` for detailed troubleshooting.
