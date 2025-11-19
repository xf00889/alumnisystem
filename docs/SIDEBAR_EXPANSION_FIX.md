# Sidebar Expansion Fix

## Issue
The documentation sidebar folder items were not expanding when clicked.

## Root Cause
The folder toggle was implemented as an anchor tag (`<a href="#">`) which was causing navigation issues and preventing the JavaScript click handler from working properly.

## Solution

### 1. Changed HTML Structure (docs/templates/docs/partials/toc.html)
- **Before**: Used `<a href="#" class="docs-toc-folder-toggle">`
- **After**: Changed to `<button type="button" class="docs-toc-folder-toggle">`

**Benefits:**
- Semantic HTML: Buttons are the correct element for interactive controls that don't navigate
- No page jumping from `href="#"`
- Better accessibility with proper button semantics
- Prevents default link behavior that was interfering with the toggle

### 2. Updated JavaScript (docs/static/docs/js/documentation.js)
- Added `e.stopPropagation()` to prevent event bubbling
- Added keyboard support for Enter and Space keys
- Improved event handling for better reliability

### 3. Updated CSS (docs/static/docs/css/documentation.css)
Added button-specific styles to ensure proper rendering:
```css
.docs-toc-folder-toggle {
    width: 100%;
    text-align: left;
    background: none;
    border: none;
    font-family: inherit;
    line-height: inherit;
}
```

## Testing
A test file has been created at `docs/test_sidebar_fix.html` to verify the fix works independently of the Django application.

To test:
1. Open `docs/test_sidebar_fix.html` in a browser
2. Click on folder items to verify they expand/collapse
3. Check that the chevron icon rotates
4. Verify keyboard navigation works (Tab to focus, Enter/Space to toggle)

## Files Modified
1. `docs/templates/docs/partials/toc.html` - Changed anchor to button
2. `docs/static/docs/js/documentation.js` - Improved event handling
3. `docs/static/docs/css/documentation.css` - Added button styles

## Verification Steps
1. Clear browser cache to ensure new CSS/JS is loaded
2. Navigate to any documentation page
3. Click on folder items in the sidebar
4. Verify folders expand and collapse smoothly
5. Check that nested folders work correctly
6. Test on mobile devices to ensure touch interaction works

## Browser Compatibility
This fix maintains compatibility with:
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Accessibility Improvements
- Proper button semantics for screen readers
- ARIA attributes maintained (`aria-expanded`)
- Keyboard navigation support (Enter/Space keys)
- Focus management preserved
