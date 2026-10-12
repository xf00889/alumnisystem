# Alumni Service Pages Redesign — Implementation Changelog

Date: October 10, 2026

## Scope

Continues the earlier Alumni Portal and Alumni Community redesign. Adds regular-alumni presentation for Donations, Surveys, Graduate Tracer Study, Feedback, the account Security Dashboard, and Notifications. Source filenames describe module responsibilities (never redesign milestone numbers).

## What changed

- **17 existing HTML templates modified**, including two shared Donations base templates and one standalone payment form. Existing form fields, data attributes, JavaScript hooks, route names, CSRF markup, and business content are preserved.
- **`core/context_processors.py`**: adds `tracer_study_page_base` to choose public/alumni/admin layout correctly; extends existing feature script availability to Donations, Surveys, Feedback for ordinary alumni.
- **6 alumni-only CSS modules added**: `donations.css`, `surveys.css`, `tracer-study.css`, `feedback.css`, `security.css`, `notifications.css` under `static/css/alumni/`.
- Regular alumni receive the existing NORSU public-site inspired university header/nav, navy/gold/cream theme and responsive UI. Staff, superusers and alumni coordinators still use the original `base.html`.
- **Standalone donation payment form** (`donations/base_donation_form.html`) conditionally embeds the alumni masthead, navigation and footer. Public and staff flows retain their standalone document layout.
- Authenticated alumni viewing the public Tracer Study index continue loading `public_tracer_studies.css`; it was previously supplied indirectly by the old base.

## Deliberately unchanged

- Admin/staff donation management, verification, campaign CRUD, fraud and analytics, survey admin/report pages, tracer report management, feedback administration, user-role/permission checks, APIs, models, views, database schema, and existing JavaScript behavior.
- External unauthenticated login, password reset, verification email, and public employer tracer form stay in their pre-existing design to avoid mixing public/authentication and alumni-only UI scopes.
- Root `templates/donations/` and app `donations/templates/donations/` have duplicate names. Both relevant base layouts and donation-history variants have been handled; full duplicate consolidation should be a separate task, after validating real template lookup order.

## Known issues, not caused by this pass

- The prior Groups map template includes an invalid Django template expression.
- A group-chat view refers to a missing template in the baseline ZIP.
- Some survey employment/achievement endpoints refer to missing templates in the baseline ZIP.
- `templates/accounts/security_dashboard.html` contains existing hardcoded illustrative IP/date/activity data that must be replaced with real audited data before it is presented as factual security history.

This is a frontend presentation change. Static checks passed; full authenticated browser and real database testing are still required.
