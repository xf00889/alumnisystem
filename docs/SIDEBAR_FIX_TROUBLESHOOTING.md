# Sidebar Expansion Fix - Troubleshooting Guide

## Changes Made

### 1. HTML Structure Fix
**File:** `docs/templates/docs/partials/toc.html`
- Changed folder toggle from `<a href="#">` to `<button type="button">`
- This prevents page navigation and CSP issues with anchor tags

### 2. CSS Updates
**File:** `docs/static/docs/css/documentation.css`
- Added button-specific styles for `.docs-toc-folder-toggle`
- Moved inline styles from `base_standalone.html` to external CSS file
- This eliminates CSP violations from inline styles

### 3. JavaScript Enhancements
**File:** `docs/static/docs/js/documentation.js`
- Added `e.stopPropagation()` to prevent event bubbling
- Added keyboard support for Enter/Space keys
- Added console logging for debugging

### 4. Removed Inline Styles
**File:** `docs/templates/docs/base_standalone.html`
- Removed all inline `<style>` tags
- Moved styles to external CSS file to comply with CSP

## Troubleshooting Steps

### Step 1: Clear Browser Cache
```
1. Open DevTools (F12)
2. Right-click the refresh button
3. Select "Empty Cache and Hard Reload"
```

### Step 2: Check Console for Errors
Open the browser console (F12) and look for these messages:
- ✓ `Documentation JS: File loaded successfully`
- ✓ `Documentation JS: Initializing...`
- ✓ `Documentation JS: Initializing TOC folders...`
- ✓ `Documentation JS: Found X TOC folders`

If you don't see these messages, the JavaScript file isn't loading.

### Step 3: Verify Static Files
Run Django's collectstatic command:
```bash
python manage.py collectstatic --noinput
```

### Step 4: Check CSP Headers
In the browser DevTools Network tab:
1. Reload the page
2. Click on the HTML document
3. Check Response Headers for `Content-Security-Policy`
4. Verify it includes:
   - `script-src 'self' 'unsafe-inline'`
   - `style-src 'self' 'unsafe-inline'`

### Step 5: Test JavaScript Loading
Navigate to: `/static/docs/js/documentation.js`
- Should download/display the JavaScript file
- If 404, run `collectstatic` again

### Step 6: Check for JavaScript Errors
Look for any errors in the console that might prevent initialization:
- Syntax errors
- Reference errors
- CSP violations

## Common Issues and Solutions

### Issue 1: CSP Blocking Inline Styles
**Symptom:** Console shows CSP violation for inline styles
**Solution:** All inline styles have been moved to external CSS file

### Issue 2: JavaScript Not Loading
**Symptom:** No console messages from documentation.js
**Solution:** 
1. Run `python manage.py collectstatic`
2. Check STATIC_URL and STATIC_ROOT settings
3. Verify WhiteNoise middleware is configured

### Issue 3: Folders Still Not Expanding
**Symptom:** Click events not firing
**Solution:**
1. Check console for "Folder clicked!" message
2. If missing, check if event listener is attached
3. Verify button element exists in DOM

### Issue 4: CSP Blocking External Scripts
**Symptom:** CSP error for CDN scripts (Bootstrap, Font Awesome)
**Solution:** Verify CSP_SCRIPT_SRC includes:
```python
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",
    "https://cdn.jsdelivr.net",
    "https://cdnjs.cloudflare.com",
)
```

## Testing Checklist

- [ ] Clear browser cache
- [ ] Check console for "Documentation JS: File loaded successfully"
- [ ] Click on a folder item in the sidebar
- [ ] Verify console shows "Documentation JS: Folder clicked!"
- [ ] Verify folder expands/collapses
- [ ] Test on mobile device
- [ ] Test keyboard navigation (Tab + Enter)
- [ ] Verify no CSP violations in console

## Debug Mode

To enable more verbose logging, you can temporarily add more console.log statements:

```javascript
// In initTOCFolders function
console.log('Toggle element:', toggle);
console.log('Content element:', content);
console.log('Folder expanded state:', folder.classList.contains('expanded'));
```

## Production Deployment

Before deploying to production:
1. Remove all console.log statements (or use a build process)
2. Run `python manage.py collectstatic --noinput`
3. Test in production environment
4. Monitor for CSP violations

## Contact

If issues persist after following this guide, check:
1. Browser console for specific error messages
2. Django logs for server-side errors
3. Network tab for failed resource loads
