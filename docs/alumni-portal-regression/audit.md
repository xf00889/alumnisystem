# Alumni Portal — Regression & Readiness Audit

Date: 2026-10-10
Baseline: `alumnisystem_alumni_services_redesign.zip` (latest regular-alumni redesign)

## Scope and methodology

Reviewed the alumni dashboard, Profile, Directory, Jobs, Mentorship, Groups, Connections, Messaging, Events, Announcements, Donations, Surveys, Tracer Study, Feedback, Security, and Notifications, and the shared alumni layout and navigation. Examined Django template inheritance, role selection, local static references, CSS and JavaScript syntax, and the Groups map view/template contract. Reviewed staff isolation by inspecting modified files and the unchanged administrator base template. Tested standalone alumni navigation interactions using headless Chromium, with Bootstrap collapse behavior simulated. **No production data or authenticated live server was available.**

## Confirmed findings and actions

| Priority | Finding | Action | Status |
|---|---|---|---|
| High | Groups map view returned no group data; a Python-style ORM query inside a Django template caused a template compilation failure. | Populate active groups, membership IDs, filter data and current year; use a valid membership test in the template. | Fixed; static checks pass |
| High | Template-generated JavaScript redeclared `const marker` for every group. | Enclosed each per-group marker in its own JS block; tested rendering with two markers. | Fixed; JS syntax passes |
| High | HR accounts with job-management privileges were receiving the ordinary alumni layout. | Preserve the previous management presentation for HR, along with staff, coordinator and superuser. | Fixed; role regression tests pass |
| Medium | The map template expected `AlumniGroup.location` and `AlumniGroup.region`, fields absent from that model; the view supplied no groups. | Restore the active-group directory/list and use the real campus field. Regular-alumni map controls are disabled with an explanatory message until a supported geographic source exists; staff chrome remains unmodified. | Partially mitigated; coordinates unavailable |
| Medium | Map popup rendered model-provided text inside a JavaScript HTML string. | Apply HTML escaping before JavaScript escaping to group name and description. | Fixed in template |
| Medium | Map nearby-location API expects `AlumniGroup.latitude`/`longitude`, which the model does not define. | Do not fabricate group coordinates, alter schema, or use alumni-member location. The unsupported nearby control is disabled for regular users. | Unresolved backend/API mismatch |
| Medium | Skill Matching page references a nonexistent `static/js/skill_matching.js`. | Retained the existing page; do not introduce fake or guessed business logic. | Unresolved existing 404; requires implementation against verified API contract |
| Medium | `core/tests/test_services.py` is malformed Python at line 4 in the baseline. | Retained unchanged; out of scope for UI redesign. | Unresolved existing test error |

## Scope of changes

Modified only:
- `alumni_groups/views.py`
- `templates/alumni_groups/group_map.html`
- `static/css/alumni/groups.css`
- `core/context_processors.py`

Added:
- `core/tests/test_alumni_layout_isolation.py`
- This audit documentation

No migration, database schema, model, route, auth permission, job submission, payment, survey, or admin template was intentionally modified. The global `base.html` remains identical to the uploaded baseline.

## Important limitations

1. The Groups map is **not a functional geographic group map** until a real group-coordinate source and its permissions are specified. Only the group list is restored; the existing `nearby_groups_api` still requires backend work.
2. Source-level static checks are not proof of correctness of forms, permissions, messaging, GCash donation proofs, tracer eligibility, database queries or browser layout on actual authenticated pages.
3. Browser smoke testing covers the navigation component with simulated Bootstrap collapse and viewport changes, not the live site running against its database.
4. Live app startup, all Django management checks, full URL resolution, external CSS/CDN availability, and end-to-end regression testing require a correctly configured local/production-like environment.

## Required deployment acceptance test

Run `python manage.py check`, resolve dependencies and database services, execute the project's test suite, then manually test regular alumni, HR, staff, coordinator and superuser accounts. Navigate all redesigned pages, submit forms with safe test data, verify access controls and modal interactions, inspect mobile/tablet/desktop sizes with real CSS/JS and capture browser console/network errors. In particular, verify Groups map data source requirements and the Skill Matching JavaScript missing-file issue before considering production readiness.
