# reCAPTCHA v3 Testing Guide

## Prerequisites
- reCAPTCHA v3 keys configured in database (Site Configuration > reCAPTCHA)
- Keys must be v3 type (not v2)

## Test Scenarios

### 1. Test with reCAPTCHA Enabled

#### Setup
1. Go to admin panel: `/admin/core/recaptchaconfig/`
2. Ensure you have an active reCAPTCHA configuration with:
   - `enabled` = True
   - `version` = v3
   - Valid `site_key` and `secret_key` (v3 keys)
   - `threshold` = 0.5 (or your preferred value)

#### Test Login
1. Navigate to `/accounts/login/`
2. Open browser console (F12)
3. Enter valid credentials
4. Click "Sign In"
5. **Expected behavior:**
   - Button shows "Please wait..." with spinner
   - Console shows no errors
   - Form submits automatically after reCAPTCHA token is generated
   - Login succeeds if credentials are valid

#### Test Signup
1. Navigate to `/accounts/login/` and click "Sign Up" tab
2. Fill in all required fields with valid data
3. Ensure password meets all requirements
4. Click "Create Account"
5. **Expected behavior:**
   - Password validation passes
   - Button shows "Please wait..." with spinner
   - Console shows no errors
   - Form submits automatically after reCAPTCHA token is generated
   - Account is created and redirected to verification page

### 2. Test with reCAPTCHA Disabled

#### Setup
1. Set environment variable: `DISABLE_RECAPTCHA=True` in `.env`
2. OR disable in database: Set `enabled` = False in reCAPTCHA config
3. Restart server or clear cache: `python manage.py clear_recaptcha_cache`

#### Test Login & Signup
1. Navigate to `/accounts/login/`
2. **Expected behavior:**
   - No reCAPTCHA script loads
   - No hidden input fields for tokens
   - Forms submit directly without reCAPTCHA
   - Login/signup works normally

### 3. Test with Invalid Keys

#### Setup
1. Configure reCAPTCHA with invalid keys in database
2. Keep `enabled` = True

#### Test
1. Try to login or signup
2. **Expected behavior:**
   - Form still submits (graceful degradation)
   - Console may show reCAPTCHA errors
   - Backend validation may fail, but form submission succeeds
   - User sees appropriate error message from backend

### 4. Test Network Failure

#### Setup
1. Open browser DevTools > Network tab
2. Block `google.com` or `recaptcha.net` domains

#### Test
1. Try to login or signup
2. **Expected behavior:**
   - reCAPTCHA script fails to load
   - Form still submits after timeout
   - Console shows error but doesn't block submission

### 5. Test Score Threshold

#### Setup
1. Set different threshold values in database (0.0 to 1.0)
2. Test with different user behaviors

#### Test
1. Normal user behavior (should get high score ~0.9)
2. Rapid form submissions (may get lower score)
3. **Expected behavior:**
   - High scores (above threshold) allow submission
   - Low scores (below threshold) show error message
   - Check backend logs for actual scores

## Debugging

### Check Console Logs
Look for these messages:
- `reCAPTCHA error:` - Indicates reCAPTCHA execution failed
- No errors = successful token generation

### Check Network Tab
1. Look for request to `https://www.google.com/recaptcha/api.js?render=YOUR_SITE_KEY`
2. Should load successfully with 200 status

### Check Form Submission
1. In Network tab, look for POST to `/accounts/login/` or `/accounts/enhanced_signup/`
2. Check Form Data section
3. Should include `g-recaptcha-response` field with token value

### Check Backend Logs
Look for reCAPTCHA validation messages in application logs:
```
INFO: reCAPTCHA validation successful, score: 0.9
WARNING: reCAPTCHA score below threshold: 0.3 < 0.5
```

## Common Issues

### Issue: "Missing required parameters: sitekey"
**Cause:** Template variable `recaptcha_site_key` is empty
**Fix:** 
1. Check database configuration has valid site_key
2. Clear cache: `python manage.py clear_recaptcha_cache`
3. Restart server

### Issue: "Invalid key type"
**Cause:** Using v2 keys with v3 implementation
**Fix:** Generate new v3 keys at https://www.google.com/recaptcha/admin

### Issue: Forms don't submit
**Cause:** JavaScript error or missing form IDs
**Fix:** 
1. Check console for errors
2. Verify form IDs: `loginFormElement`, `signupFormElement`
3. Check button IDs: `loginSubmitBtn`, `signupSubmitBtn`

### Issue: reCAPTCHA works locally but not on hosting
**Cause:** Cache not cleared or environment variable not set
**Fix:**
1. Run: `python manage.py clear_recaptcha_cache`
2. Add to `build.sh`: `python manage.py clear_recaptcha_cache`
3. Check environment variables on hosting platform

## Success Criteria

✅ Login form submits with valid credentials
✅ Signup form creates new accounts
✅ reCAPTCHA tokens are generated and submitted
✅ Forms work when reCAPTCHA is disabled
✅ No console errors during normal operation
✅ Graceful degradation when reCAPTCHA fails
✅ Backend validation accepts v3 tokens
✅ Score threshold is enforced correctly

## Production Deployment Checklist

- [ ] v3 keys configured in production database
- [ ] `DISABLE_RECAPTCHA` not set to True in production
- [ ] Cache cleared after deployment
- [ ] Test login with real user account
- [ ] Test signup with new email
- [ ] Monitor backend logs for reCAPTCHA scores
- [ ] Adjust threshold if too many false positives/negatives
- [ ] Verify forms work on mobile devices
- [ ] Check HTTPS is enabled (required for reCAPTCHA)

## Monitoring

### Metrics to Track
1. reCAPTCHA validation success rate
2. Average scores for legitimate users
3. Number of submissions blocked by low scores
4. reCAPTCHA API errors

### Logs to Monitor
```bash
# Check for reCAPTCHA errors
grep "reCAPTCHA" logs/alumni_system.log

# Check validation failures
grep "score below threshold" logs/alumni_system.log

# Check API errors
grep "reCAPTCHA API error" logs/errors.log
```
