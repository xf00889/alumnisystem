# Quick Fix Reference - Sidebar Not Expanding

## Immediate Actions

### 1. Clear Browser Cache
**Windows/Linux:** `Ctrl + Shift + Delete`
**Mac:** `Cmd + Shift + Delete`

Or in DevTools:
1. Open DevTools (F12)
2. Right-click refresh button
3. Select "Empty Cache and Hard Reload"

### 2. Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### 3. Restart Development Server
```bash
# Stop server (Ctrl+C)
python manage.py runserver
```

## Quick Diagnostics

### Open Browser Console (F12)
Look for these messages:
```
✓ Documentation JS: File loaded successfully
✓ Documentation JS: Initializing...
✓ Documentation JS: Found X TOC folders
```

### Click a Folder
Should see:
```
✓ Documentation JS: Folder clicked!
```

## If Still Not Working

### Check 1: Static Files Location
Navigate to: `http://localhost:8000/static/docs/js/documentation.js`
- Should download the file
- If 404, run `collectstatic` again

### Check 2: CSP Settings
In `norsu_alumni/settings.py`, verify:
```python
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",
    # ... other sources
)
```

### Check 3: Template Loading
View page source, look for:
```html
<button type="button" class="docs-toc-folder-toggle">
```
If you see `<a href="#"` instead, templates didn't update.

## Common Fixes

| Problem | Solution |
|---------|----------|
| No console messages | Run `collectstatic`, clear cache |
| CSP errors | Check `settings.py` CSP configuration |
| Folders are `<a>` tags | Clear template cache, restart server |
| Click does nothing | Check console for errors |
| Works on some pages only | Clear browser cache completely |

## Emergency Rollback

If you need to revert:
```bash
git checkout HEAD -- docs/templates/docs/partials/toc.html
git checkout HEAD -- docs/static/docs/js/documentation.js
git checkout HEAD -- docs/static/docs/css/documentation.css
python manage.py collectstatic --noinput
```

## Test Page

Open: `docs/test_sidebar_fix.html` in browser
- Standalone test without Django
- Should work immediately
- If this works but site doesn't, it's a Django config issue

## Success Indicators

- ✅ Folders expand/collapse smoothly
- ✅ Chevron rotates
- ✅ Folder icon changes
- ✅ No console errors
- ✅ Works on mobile

## Still Stuck?

1. Check `docs/SIDEBAR_FIX_TROUBLESHOOTING.md` for detailed steps
2. Review `docs/SIDEBAR_FIX_SUMMARY.md` for complete changes
3. Look at browser Network tab for failed requests
4. Check Django logs for errors

---

**Quick Command Sequence:**
```bash
python manage.py collectstatic --noinput
# Restart server
# Clear browser cache (Ctrl+Shift+Delete)
# Test
```
