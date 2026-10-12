# Alumni dashboard foundation — Alumni Portal Redesign (2026-10-10)

## Scope

Alumni dashboard foundation establishes an authenticated alumni-only design system matching the existing public website's NORSU identity. It redesigns the **regular alumni dashboard only** and provides the base layout and reusable components for subsequent pages.

## Changes

- `core/views.py`: selects `alumni/dashboard.html` for authenticated regular alumni who have completed registration. Staff and alumni coordinators keep `authenticated_home.html`; superusers keep the existing redirect to the admin dashboard. No models, route names, URL patterns, permissions, or data queries were changed.
- `templates/base_alumni.html`: isolated alumni shell with existing university masthead and footer, tracer reminder, toast messages, bootstrap, and existing core frontend service scripts.
- `templates/alumni/components/navigation.html`: responsive logged-in alumni navigation and menus, including a direct link to the public survey list rather than admin survey management.
- `templates/alumni/components/quick_link.html` and `empty_state.html`: reusable view components.
- `templates/alumni/dashboard.html`: redesigned dashboard with profile welcome, six navigation actions, announcements, upcoming events, and community call-to-action. Uses unchanged `announcements` and `upcoming_events` context data.
- `static/css/alumni/layout.css`, `components.css`, and `dashboard.css`: scoped navy / gold / paper styling, matching the existing public design palette.
- `static/js/alumni/navigation.js`: mobile menu keyboard and outside-click behavior.

## Audience isolation

- Regular logged-in alumni: new alumni layout, dashboard, and CSS.
- Staff/alumni coordinators: unchanged `authenticated_home.html` and admin sidebar layout.
- Superuser: unchanged `core:admin_dashboard` redirect.
- Anonymous: unchanged `base_landingpage.html` and public page views.
- **Other alumni pages currently retain their original templates and assets.** Migrating them is subsequent alumni feature redesigns and should be done with appropriate admin/user template separation.

## Validation performed

- Django 5.0.2 template compilation of six newly added templates using the project's bundled Django package: passed.
- Python AST parsing of modified view: passed.
- JavaScript syntax check using `node --check`: passed.
- CSS parsing using `tinycss2`: passed for all three new files.
- All new static and template includes exist: passed.
- New namespaced route names found in their corresponding existing Django URL configurations: passed.
- The original staff dashboard template remained byte-identical: passed.
- Archive integrity: see accompanying report for results.

## Not verified / known limitations

A working Django environment with all project dependencies, database services, and test users was not available for complete startup, role-based HTTP checks, browser rendering, or end-to-end regression tests. Route-name checks are static and not full runtime `reverse()` checks. Existing unrelated source issues from the cleanup audit remain.

## Local smoke tests

1. Create/use a Django environment and install the existing `requirements.txt` (the lightweight ZIP intentionally excludes `venv/`).
2. Run `python manage.py check` and any existing tests that run in your environment.
3. Run `python manage.py collectstatic --noinput` in the intended deployment configuration.
4. Sign in as a regular alumni user and open `/`: confirm the masthead, navy navigation, hero, announcements and events, and mobile menu (at approximately 375px, 768px, 1024px widths).
5. Sign in as a staff member or alumni coordinator: confirm the **old** dashboard and admin/sidebar behavior remain unchanged.
6. Sign in as a superuser: confirm redirect to admin dashboard. Open the public homepage without signing in and confirm unchanged public navigation.
7. Verify navigation to directory, jobs, mentorship, groups, messages, announcements, events, donations and public surveys. Confirm there is no access to admin-only survey management through the alumni menu.
8. Confirm notification badge/toasts and previously supported location tracking under a real logged-in account, observing opt-out preferences.

## Rollback

Revert `core/views.py` to its previous content and optionally delete the newly added `templates/base_alumni.html`, `templates/alumni/`, `static/css/alumni/`, and `static/js/alumni/`. The previous `templates/authenticated_home.html` remains unchanged.

## Important

This is a layout/design milestone, **not a production-readiness certification**. Do not use visually successful previews in place of authenticated browser and permission tests.
