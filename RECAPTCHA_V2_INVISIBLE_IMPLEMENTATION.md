# reCAPTCHA v2 Invisible Implementation - COMPLETED

## Problem
User was using reCAPTCHA v2 Invisible but the login/signup forms were configured for v2 Checkbox. After passing the reCAPTCHA challenge, the form wouldn't submit automatically.

## Solution Implemented

### 1. Database Model Support
- Updated `core/models/recaptcha_config.py` to support three distinct versions:
  - `v2_checkbox` - Shows checkbox widget, user must click
  - `v2_invisible` - Hidden widget, executes on submit, shows challenge only if suspicious
  - `v3` - Score-based, no user interaction

### 2. Context Processor
- Updated `core/context_processors.py` to pass `recaptcha_version` to all templates
- Normalizes legacy 'v2' to 'v2_checkbox' for clarity

### 3. Utility Functions
- Updated `core/recaptcha_utils.py`:
  - `get_recaptcha_version()` returns the configured version
  - Defaults to 'v2_invisible' for better UX
  - Normalizes legacy 'v2' to 'v2_checkbox'

### 4. Template Updates (`templates/account/login.html`)

#### HTML Changes
- Conditionally renders v2 Checkbox OR v2 Invisible widget based on `recaptcha_version`
- v2 Invisible widgets have `data-size="invisible"` attribute
- Both login and signup forms support both versions

#### JavaScript Changes

**Callback Functions:**
```javascript
function onLoginRecaptchaSuccess(token) {
    document.getElementById('loginCaptchaToken').value = token;
    
    // For v2 Invisible, auto-submit after token received
    if (isRecaptchaExecuting) {
        isRecaptchaExecuting = false;
        loginForm.submit();
    }
}
```

**Form Submission Handlers:**
```javascript
// For v2 Invisible
if (!captchaToken && !isRecaptchaExecuting) {
    e.preventDefault();
    isRecaptchaExecuting = true;
    grecaptcha.execute(widgetId);  // Execute invisible reCAPTCHA
    return;
}

// For v2 Checkbox
if (!captchaToken) {
    e.preventDefault();
    showError('Please complete the reCAPTCHA verification');
    return;
}
```

## How It Works

### v2 Checkbox Flow:
1. User fills form
2. User clicks reCAPTCHA checkbox
3. Challenge appears (if needed)
4. Token is set via callback
5. User clicks submit
6. Form validates token exists
7. Form submits

### v2 Invisible Flow:
1. User fills form
2. User clicks submit
3. Form validation runs
4. `grecaptcha.execute()` is called
5. reCAPTCHA runs in background
6. Challenge appears only if suspicious activity detected
7. Token is set via callback
8. Callback auto-submits the form

## Configuration

### Admin UI
The reCAPTCHA configuration form at `/cms/site-config/recaptcha/` now shows:
- v2 Checkbox (I'm not a robot checkbox)
- v2 Invisible (Verifies in background)
- v3 (Score-based, no interaction)

### Environment Variables
- `DISABLE_RECAPTCHA=True` - Emergency override to disable reCAPTCHA completely

## Testing

### Test v2 Checkbox:
1. Set version to "v2 Checkbox" in admin
2. Visit login page
3. Should see checkbox widget
4. Must click checkbox before submitting

### Test v2 Invisible:
1. Set version to "v2 Invisible" in admin
2. Visit login page
3. Should NOT see any widget
4. Click submit - form should submit automatically
5. Challenge only appears if Google detects suspicious activity

## Files Modified
- `core/models/recaptcha_config.py` - Added v2_invisible choice
- `core/migrations/0018_update_recaptcha_version_choices.py` - Migration
- `core/context_processors.py` - Added recaptcha_version to context
- `core/recaptcha_utils.py` - Updated get_recaptcha_version()
- `templates/account/login.html` - Conditional rendering and JavaScript
- `templates/recaptcha_configuration_form.html` - Updated UI

## Notes
- v2 Invisible provides better UX as users don't need to click checkbox
- Challenge still appears if Google detects suspicious activity
- Both versions use the same site key and secret key
- The version can be changed in admin without code changes
