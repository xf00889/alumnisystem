# Frontend Refactoring Changelog — 2026-10-10

## Files affected

- **Changed source templates:** 168 files detected as differing from the original for the counted HTML/static categories.
- **New consolidated CSS files:** 26.
- **New consolidated JS files:** 12.
- **CSS style blocks extracted:** 156.
- **JS script blocks extracted:** 33.
- **Existing templates deleted:** 0.
- **Backend source code modified:** 0.

### New stylesheets
- `static/css/modules/account.css` (21,880 bytes)
- `static/css/modules/accounts.css` (157,930 bytes)
- `static/css/modules/admin.css` (78,196 bytes)
- `static/css/modules/alumni-directory.css` (85,821 bytes)
- `static/css/modules/alumni-groups.css` (197,056 bytes)
- `static/css/modules/announcements.css` (83,263 bytes)
- `static/css/modules/cms-app.css` (220,929 bytes)
- `static/css/modules/connections.css` (96,557 bytes)
- `static/css/modules/core.css` (10,543 bytes)
- `static/css/modules/donations-app.css` (122,677 bytes)
- `static/css/modules/donations.css` (95,135 bytes)
- `static/css/modules/events.css` (58,364 bytes)
- `static/css/modules/feedback.css` (65,742 bytes)
- `static/css/modules/jobs-app.css` (99,095 bytes)
- `static/css/modules/jobs.css` (12,047 bytes)
- `static/css/modules/layout-authenticated.css` (6,766 bytes)
- `static/css/modules/layout-public.css` (19,700 bytes)
- `static/css/modules/log-viewer-app.css` (46,752 bytes)
- `static/css/modules/mentorship-app.css` (18,060 bytes)
- `static/css/modules/mentorship.css` (59,325 bytes)
- `static/css/modules/setup-app.css` (9,556 bytes)
- `static/css/modules/socialaccount.css` (13,541 bytes)
- `static/css/modules/surveys-app.css` (15,922 bytes)
- `static/css/modules/surveys.css` (108,352 bytes)
- `static/css/modules/system.css` (114,281 bytes)
- `static/css/modules/tracer-study.css` (17,747 bytes)

### New scripts
- `static/js/modules/accounts.js` (15,978 bytes)
- `static/js/modules/admin.js` (11,132 bytes)
- `static/js/modules/alumni-directory.js` (654 bytes)
- `static/js/modules/alumni-groups.js` (6,978 bytes)
- `static/js/modules/announcements.js` (1,615 bytes)
- `static/js/modules/cms-app.js` (16,703 bytes)
- `static/js/modules/donations-app.js` (13,749 bytes)
- `static/js/modules/events.js` (3,230 bytes)
- `static/js/modules/feedback.js` (3,667 bytes)
- `static/js/modules/landing.js` (6,277 bytes)
- `static/js/modules/system.js` (6,026 bytes)
- `static/js/modules/tracer-study.js` (3,588 bytes)

### Template edits

For each affected template, see `asset-inventory.csv` and `app-template-inventory.csv`. They record whether the CSS or JavaScript block was moved or deliberately retained and provide the reason.

### Notes

- App source assets are separated from project override assets to avoid accidental CSS or JS collisions if Django template-loader precedence changes.
- No unused template, component or static asset was deleted without usage proof.
- Re-run `collectstatic` and perform browser acceptance tests before deployment.
