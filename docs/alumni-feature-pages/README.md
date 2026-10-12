# Alumni feature-page redesign — Regular-alumni frontend redesign (10 Oct 2026)

## Scope and visual direction

The Alumni dashboard foundation authenticated alumni shell (`templates/base_alumni.html`) now powers **17 regular alumni page templates** for Profile, Alumni Directory, Job Board and Mentorship. The navy/gold/cream palette, Poppins interface type, responsive cards and dedicated navigation align with the public website. This is a presentation-only refactor; the existing forms, IDs, URLs, field names, Javascript hooks, view context, queries, business workflows and endpoint contracts remain unchanged.

### Profile (6)
- `templates/accounts/profile_detail.html`
- `templates/accounts/profile_update.html`
- `templates/accounts/edit_profile.html`
- `templates/accounts/skill_matching.html`
- `templates/accounts/mentor_application_form.html`
- `templates/accounts/mentor_application_status.html`

### Directory (3)
- `templates/alumni_directory/alumni_list.html`
- `templates/alumni_directory/alumni_detail.html`
- `templates/alumni_directory/tabular_alumni_list.html`

### Jobs (3)
- `jobs/templates/jobs/job_list.html`
- `jobs/templates/jobs/job_detail.html`
- `jobs/templates/jobs/apply.html`

### Mentorship (5)
- `templates/mentorship/mentor_search.html`
- `templates/mentorship/request_mentorship.html`
- `templates/mentorship/mentor_dashboard.html`
- `templates/mentorship/mentee_dashboard.html`
- `templates/mentorship/requests_list.html`

## Implementation

- Added `alumni_page_base` and `use_alumni_layout` presentation context in the existing `core.context_processors.user_role_context`.
- Regular authenticated users (not staff, superusers or alumni coordinators) inherit `base_alumni.html`; everyone else inherits unchanged `base.html`.
- Every opted-in shared template switches only its template parent, adds a conditional breadcrumb partial, and includes CSS for regular alumni only. Original template bodies and existing asset loads remain untouched.
- Added `templates/alumni/components/breadcrumbs.html`.
- Added `static/css/alumni/page-foundation.css`, `profile.css`, `directory.css`, `jobs.css` and `mentorship.css`.
- Alumni dashboard foundation alumni base now loads vendor dependencies only for regular-alumni feature routes in Alumni feature-page redesign (`accounts`, `alumni_directory`, `jobs`, `mentorship`): tagsinput, Chart.js, SweetAlert2, and htmx, with jQuery and Bootstrap loaded first. The basic dashboard does not incur those extra scripts.
- **No new JavaScript**: original functions and existing JS remain in use. No new routes, middleware, database migrations, packages or role permissions.

## Staff and admin isolation

Staff, superusers and alumni coordinators still use `base.html`. None of their views, their sidebar, their base CSS, or their template bodies have been redesigned. New CSS loads only under `use_alumni_layout` and uses `body.alumni-portal` scoping.

## Known risks and validation limits

- Passed Python syntax for changed code, CSS parsing for all five new stylesheets, token-level inspection of all 17 changed templates, static asset-path checks, and mocked presentation-role tests for anonymous/staff/superuser/coordinator/alumni.
- Compared all 17 modified page template bodies with their Alumni dashboard foundation originals after removing only the explicit presentation additions; no other template-body changes.
- Confirmed backend view files and admin base remained byte-for-byte identical.
- **Full running-Django render, authenticated interactions, responsive-browser screenshots and end-to-end tests were not executed**. The app's Windows virtual environment is not executable in the Linux validation container. Existing pre-Feature-page defects from previous verification remain outside this change.
- A true accessibility, filter, application form, mentor scheduling and interactive regression run is needed before production deployment.

## QA checklist

1. Regular alumni: open dashboard, profile (own and another user's), edit profile, mentor application and skill-matching screens.
2. Regular alumni: directory list, search, detail modal, detail page and tabular view/export.
3. Regular alumni: job filters, preference modal, AI ranking controls, job detail and job application submission.
4. Regular alumni: mentor search (including dynamic results), request modal/page, mentor and mentee dashboards, and requests list.
5. Staff, coordinator and superuser: open each shared page and confirm original admin sidebar and styles remain intact.
6. On phones/tablets: verify header/nav collapse, scrollable tables, filter sheet, profile forms and modal dialogs.
7. Check browser console and network tab for JS errors, broken static resources, and unexpected 403/404 responses.

Phase 3 (groups, connections, chat, events, announcements) is not implemented here.
