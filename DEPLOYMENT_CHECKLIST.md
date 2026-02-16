# Deployment Checklist - reCAPTCHA Fix

## Files Changed (Ready to Deploy)

### Code Changes
- ✅ `core/recaptcha_utils.py` - Added emergency override
- ✅ `norsu_alumni/settings.py` - Added DISABLE_RECAPTCHA setting
- ✅ `.env.example` - Documented new option
- ✅ `accounts/forms.py` - Already had proper fallback (no changes needed)
- ✅ `templates/account/login.html` - Already had safe validation (no changes needed)
- ✅ `build.sh` - Already has cache clearing (no changes needed)

### New Migration
- ✅ `core/migrations/0017_alter_ssoconfig_provider.py` - SSO provider field update

### Documentation
- ✅ `RECAPTCHA_HOSTING_FIX_NOW.md` - Immediate action guide
- ✅ `QUICK_FIX_HOSTING.md` - Quick reference
- ✅ `RECAPTCHA_FIX.md` - Detailed troubleshooting
- ✅ `RECAPTCHA_SOLUTION_SUMMARY.md` - Complete overview
- ✅ `DEPLOYMENT_CHECKLIST.md` - This file

## Pre-Deployment Steps

### 1. Commit All Changes
```bash
git add .
git commit -m "Fix: Add emergency override for reCAPTCHA + pending SSO migration"
git push origin main
```

### 2. Verify Locally (Optional)
```bash
# Check no pending migrations
python manage.py makemigrations --check

# Verify reCAPTCHA is disabled
python manage.py shell -c "from core.recaptcha_utils import is_recaptcha_enabled; print(f'reCAPTCHA: {is_recaptcha_enabled()}')"
```

Expected output: `reCAPTCHA: False`

## Deployment Options

### Option A: Deploy + Environment Variable (RECOMMENDED)

**Best for:** Immediate fix with guaranteed success

1. **Push code to repository**
   ```bash
   git push origin main
   ```

2. **Add environment variable in Render BEFORE deployment completes**
   - Go to Render dashboard
   - Click "Environment" tab
   - Add: `DISABLE_RECAPTCHA=True`
   - Save changes

3. **Wait for deployment to complete**
   - Build script will run migrations
   - Build script will clear cache
   - Application will restart with override active

4. **Test login**
   - Should work immediately

5. **Remove environment variable after confirming**
   - Delete `DISABLE_RECAPTCHA` from Environment tab
   - Save changes

### Option B: Deploy Only (Let Cache Clear Work)

**Best for:** If you want to rely on the cache clearing in build script

1. **Push code to repository**
   ```bash
   git push origin main
   ```

2. **Wait for deployment to complete**
   - Build script will run migrations
   - Build script will clear cache
   - Application will restart

3. **Test login**
   - Should work after cache is cleared

4. **If still not working**
   - Add `DISABLE_RECAPTCHA=True` environment variable
   - Follow Option A steps 2-5

## Post-Deployment Verification

### 1. Check Deployment Logs
Look for these success messages:
```
✅ Running database migrations...
✅ Applying core.0017_alter_ssoconfig_provider... OK
✅ Clearing reCAPTCHA cache...
✅ reCAPTCHA cache cleared successfully!
✅ Build completed successfully!
```

### 2. Verify reCAPTCHA Status
SSH into hosting or use console:
```bash
python manage.py shell -c "from core.recaptcha_utils import is_recaptcha_enabled; print(f'reCAPTCHA: {is_recaptcha_enabled()}')"
```

Expected: `reCAPTCHA: False`

### 3. Test Login
1. Open login page (use incognito/private window)
2. Should NOT see reCAPTCHA widget
3. Enter credentials
4. Click "Sign In"
5. Should login successfully ✅

### 4. Test Signup
1. Click "Sign Up" tab
2. Should NOT see reCAPTCHA widget
3. Fill in form
4. Click "Create Account"
5. Should proceed to verification ✅

## Troubleshooting

### Issue: Migration fails
**Error:** `django.db.utils.OperationalError`

**Solution:**
1. Check database connection
2. Verify database user has migration permissions
3. Try manual migration:
   ```bash
   python manage.py migrate core 0017
   ```

### Issue: Still seeing "Security Verification Required"
**Cause:** Cache not cleared or still cached

**Solution:**
1. Add `DISABLE_RECAPTCHA=True` environment variable
2. Restart application
3. Test again

### Issue: reCAPTCHA widget still appears
**Cause:** Browser cache or template cache

**Solution:**
1. Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
2. Clear browser cache completely
3. Try incognito/private window

### Issue: Environment variable not working
**Cause:** Typo or wrong value

**Solution:**
1. Verify exact spelling: `DISABLE_RECAPTCHA` (all caps)
2. Verify value: `True` (capital T)
3. Restart application after adding
4. Check logs for confirmation

## Rollback Plan (If Needed)

### If deployment fails:
1. **Revert code changes:**
   ```bash
   git revert HEAD
   git push origin main
   ```

2. **Or rollback in Render:**
   - Go to "Manual Deploy"
   - Select previous successful deployment
   - Click "Rollback to this version"

### If login still broken after deployment:
1. **Add emergency override:**
   - Set `DISABLE_RECAPTCHA=True` in environment
   - This will work regardless of code state

2. **Clear all cache manually:**
   ```bash
   python manage.py shell -c "from django.core.cache import cache; cache.clear()"
   ```

## Success Criteria

- ✅ Deployment completes without errors
- ✅ Migration 0017 applied successfully
- ✅ reCAPTCHA cache cleared
- ✅ Login page does NOT show reCAPTCHA widget
- ✅ Login works without "Security Verification Required" alert
- ✅ Signup works without reCAPTCHA errors

## Timeline

- **Code push:** Immediate
- **Deployment:** 3-5 minutes
- **Migration:** 10-30 seconds
- **Cache clear:** 1-2 seconds
- **Total:** ~5 minutes

## Support

If you encounter any issues:
1. Check deployment logs for errors
2. Verify environment variables are set correctly
3. Try the emergency override (Option A)
4. Review `RECAPTCHA_FIX.md` for detailed troubleshooting

---

**Ready to deploy?** Follow Option A for guaranteed success!
