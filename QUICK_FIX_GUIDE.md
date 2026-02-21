# Quick Fix Guide - SSO & reCAPTCHA Not Showing

## 🚀 Quick Fix (30 seconds)

```bash
# Run this command
python manage.py check_login_config --fix

# Restart your server
# Press Ctrl+C to stop, then:
python manage.py runserver

# Clear browser cache (Ctrl+Shift+R) and test
```

## ✅ What Was Fixed

The context processor now provides both `sso_providers` and `enabled_sso_providers` to templates, fixing the variable name mismatch that prevented SSO buttons from displaying.

## 🔍 Verify It's Working

### Check Configuration:
```bash
python manage.py check_login_config
```

### Expected Output:
```
✓ SSO providers: google
✓ reCAPTCHA enabled
✓ reCAPTCHA public key configured
✓ All configurations look good!
```

## 🐛 Still Not Working?

### 1. Check Database (Django Admin)
- SSO: `/admin/core/ssoconfig/`
  - ✓ `is_active` = True
  - ✓ `enabled` = True
  
- reCAPTCHA: `/admin/core/recaptchaconfig/`
  - ✓ `enabled` = True

### 2. Clear Everything
```bash
# Clear Django cache
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
>>> exit()

# Clear browser cache
# Ctrl+Shift+R or test in incognito mode
```

### 3. Check Login Page
Navigate to: `/accounts/login/`

Should see:
- ✓ "Continue with Google" button (if SSO enabled)
- ✓ reCAPTCHA badge in bottom-right corner (if reCAPTCHA enabled)

## 📞 Need More Help?

Run the diagnostic script:
```bash
python manage.py shell < check_sso_recaptcha_config.py
```

Read the full guide:
- `SSO_RECAPTCHA_TROUBLESHOOTING.md` - Complete troubleshooting
- `FIX_SUMMARY.md` - Detailed fix explanation

## 🎯 Common Issues

| Issue | Solution |
|-------|----------|
| Button not showing | Run `check_login_config --fix` |
| OAuth fails | Check Client ID/Secret in admin |
| reCAPTCHA fails | Check Site Key/Secret in admin |
| Still not working | Clear cache + restart server |

## ✨ That's It!

The fix is applied. Just run the command, restart your server, and test!
