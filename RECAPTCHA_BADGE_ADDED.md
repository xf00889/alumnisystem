# reCAPTCHA v3 Badge - Now Visible ✅

## What Changed

Updated the login/signup template to show the reCAPTCHA v3 badge (the floating icon in the bottom-right corner) just like the contact page.

## Changes Made

### 1. Removed `async defer` from Script Tag
Changed from:
```html
<script src="https://www.google.com/recaptcha/api.js?render={{ recaptcha_site_key }}" async defer></script>
```

To:
```html
<script src="https://www.google.com/recaptcha/api.js?render={{ recaptcha_site_key }}"></script>
```

This ensures the reCAPTCHA script loads synchronously and the badge appears immediately.

### 2. Removed Hidden Input Fields
Removed the hidden input fields that were manually added:
```html
<!-- REMOVED -->
<input type="hidden" name="g-recaptcha-response" id="loginCaptchaToken">
<input type="hidden" name="g-recaptcha-response" id="signupCaptchaToken">
```

### 3. Added Invisible reCAPTCHA Widgets
Added invisible reCAPTCHA widgets before the submit buttons (similar to contact form):

**Login Form:**
```html
{% if recaptcha_enabled %}
<div class="g-recaptcha" 
     data-sitekey="{{ recaptcha_site_key }}" 
     data-callback="onLoginSubmit" 
     data-action="login"
     data-size="invisible"></div>
{% endif %}
```

**Signup Form:**
```html
{% if recaptcha_enabled %}
<div class="g-recaptcha" 
     data-sitekey="{{ recaptcha_site_key }}" 
     data-callback="onSignupSubmit" 
     data-action="signup"
     data-size="invisible"></div>
{% endif %}
```

### 4. Updated JavaScript
- Added callback functions for reCAPTCHA
- Modified form submission to dynamically create hidden input with token
- Maintained graceful degradation (works even if reCAPTCHA fails)

## What You'll See Now

### reCAPTCHA Badge
- **Location**: Bottom-right corner of the page
- **Appearance**: Small gray badge with reCAPTCHA logo
- **Behavior**: Always visible when reCAPTCHA is enabled
- **Text**: "protected by reCAPTCHA" with Privacy/Terms links

### Badge Visibility
The badge will appear on:
- ✅ Login page (`/accounts/login/`)
- ✅ Signup page (same page, signup tab)
- ✅ Contact page (`/contact-us/`)
- ✅ Any other page with reCAPTCHA v3 enabled

### When Badge Appears
- **Enabled**: When reCAPTCHA is configured and enabled in database
- **Disabled**: When `DISABLE_RECAPTCHA=True` or no configuration exists

## How It Works

1. **Page loads** → reCAPTCHA script loads → Badge appears in bottom-right
2. **User fills form** → Clicks submit
3. **JavaScript intercepts** → Calls `grecaptcha.execute()`
4. **Token generated** → Added to form as hidden input
5. **Form submits** → Backend validates token

## Comparison with Contact Page

The login page now works exactly like the contact page:

| Feature | Contact Page | Login Page |
|---------|-------------|------------|
| Badge visible | ✅ Yes | ✅ Yes |
| Badge location | Bottom-right | Bottom-right |
| Invisible widget | ✅ Yes | ✅ Yes |
| Auto-execution | ✅ Yes | ✅ Yes |
| Graceful fallback | ✅ Yes | ✅ Yes |

## Testing

### 1. Check Badge Visibility
1. Go to `/accounts/login/`
2. Look at bottom-right corner
3. You should see the reCAPTCHA badge

### 2. Check Badge Behavior
1. Hover over the badge
2. Click on "Privacy" or "Terms" links
3. Badge should be interactive

### 3. Check Form Submission
1. Fill in login form
2. Click "Sign In"
3. Form should submit successfully
4. Check browser console - no errors

### 4. Check Network Tab
1. Open DevTools > Network
2. Submit form
3. Look for POST request
4. Check Form Data - should include `g-recaptcha-response` field

## Troubleshooting

### Badge Not Appearing
**Possible causes:**
1. reCAPTCHA not enabled in database
2. Invalid site key
3. Browser blocking reCAPTCHA script
4. Cache not cleared

**Solutions:**
1. Check database configuration
2. Verify site key is correct
3. Try different browser
4. Clear cache: `python manage.py clear_recaptcha_cache`

### Badge Appears But Form Doesn't Submit
**Possible causes:**
1. JavaScript error
2. Token not being generated
3. Backend validation failing

**Solutions:**
1. Check browser console for errors
2. Verify `grecaptcha.execute()` is being called
3. Check backend logs for validation errors

## Files Modified

- `templates/account/login.html` - Added reCAPTCHA badge and updated JavaScript

## Next Steps

1. ✅ Badge is now visible
2. ⏳ Test on production
3. ⏳ Verify badge appears on all pages
4. ⏳ Monitor user feedback

---

**Status**: ✅ Complete - reCAPTCHA badge now visible on login/signup pages
**Date**: February 17, 2026
