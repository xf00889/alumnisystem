# Alumni Community Redesign — Verification

Date: October 10, 2026

| Check | Result |
|---|---|
| Original business-facing template route names, CSRF tokens, `<form>` elements and DOM hooks | 23/23 preserved by comparison against input ZIP |
| Syntax of six new CSS files using `tinycss2` | Passed |
| New CSS file references and breadcrumb include | All resolved |
| Role and dependency loading checks against the actual context processor | 35 cases passed (alumni, staff, superuser, coordinator and anonymous) |
| Django template parser with nonproduction filter stubs | 22/23 compiled; Group Map has a pre-existing invalid Django template expression |
| Original administrative `base.html` | Byte-for-byte unchanged |
| Other application source files outside the explicit change set | Byte-for-byte unchanged |
| New JavaScript files | None (all existing JS and API workflows retained) |
| ZIP integrity | Checked during output packaging |
| Full Django startup/database tests | Not run |
| Authenticated browser, mobile and accessibility regression testing | Not run |

## Known existing blockers

1. `templates/alumni_groups/group_map.html` uses `{% if not group.memberships.filter(user=user).exists %}`, which the standard Django template parser rejects. The exact expression is present in the original ZIP.
2. `connections/views.py` refers to `connections/group_chat_detail.html`, which is not available in the input ZIP. The redesign did not modify this route or create a replacement.
3. Runtime imports for the application's full stack and connected database services were not available for complete integration testing.

## Recommended local acceptance

1. Log in as regular alumni and verify all 23 pages, including responsive breakpoints, filters, moderation workflows, RSVP, and messaging send/receive and HTMX refresh.
2. Log in as staff, coordinator and superuser and compare to the pre-redesign templates.
3. Confirm CDN access (Bootstrap, SweetAlert2, HTMX, Font Awesome, Leaflet on map).
4. Run `python manage.py check`, test suite and browser smoke tests using an environment configured with this project's requirements.
5. Resolve the documented existing missing-template and invalid-template issues separately.

Do not deploy based solely on these static checks.
