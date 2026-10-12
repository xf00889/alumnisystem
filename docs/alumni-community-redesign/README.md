# Alumni Community Redesign — Changelog

Date: October 10, 2026

## Scope

Builds on the existing renamed Alumni Portal redesign; no stage numbers are used in source filenames, directories, or added component identifiers.

- **Alumni Groups:** 13 full-page templates, including browse/detail, map, creation steps, joining/leaving, membership and moderation.
- **Connections:** 4 full-page templates for requests, connections, conversation listing, direct messaging.
- **Mentorship Messages:** 1 HTMX conversation workspace.
- **Events:** 3 full-page templates for discovery, detail and registered events.
- **Announcements:** 2 full-page templates for feed and detail.

**23 full pages receive regular-alumni-only styling and layout selection.** Existing Django template inheritance dynamically selects `base_alumni.html` for regular alumni and the original `base.html` for everyone else.

## New CSS

- `static/css/alumni/community.css` — shared page headers, filtering, controls, tables, cards and responsive components.
- `static/css/alumni/groups.css` — groups presentation and map sidebar.
- `static/css/alumni/connections.css` — people/connection cards and request lists.
- `static/css/alumni/messaging.css` — direct and mentorship messaging workspaces.
- `static/css/alumni/events.css` — events discovery and registration presentation.
- `static/css/alumni/announcements.css` — feeds, urgency indicators and detail cards.

Every new stylesheet is isolated to `body.alumni-portal`. The `data-feature` on the alumni main element narrows module-specific overrides. Shared legacy module CSS and JavaScript remain in place; no backend API, database, URL, permission or business-rule changes were made.

## Existing files updated

- `core/context_processors.py`: enable existing alumni vendor-script bundle on Groups, Connections, Events and Announcements (SweetAlert2, HTMX, etc.). Staff and admins continue to use existing dependencies.
- `templates/base_alumni.html`: add feature attribute to the authenticated alumni main element.
- 22 templates under `templates/alumni_groups/`, `templates/connections/`, `templates/events/`, `templates/announcements/`.
- `mentorship/templates/mentorship/messaging/messaging_page.html`: alumni-only layout and styles; avoid double-loading HTMX/Bootstrap in alumni mode only.

## Important refinements

- Alumni Events and Announcements no longer show staff bulk-selection/deletion controls; admin versions are unaffected. Backend permissions still enforce authorization.
- Reuse of existing breadcrumbs with a conditional fallback for the My Events page.
- All existing element IDs, input names, form actions, CSRF tokens, AJAX endpoints, buttons, script handlers and dynamic message partials were preserved.
- Existing workflow-step route names (`group_create_phase1`, `group_create_phase2`) stay unchanged because they describe the actual two-step user workflow.

## Out of scope

- Public event/announcement pages; administrative CRUD forms; asynchronous HTML partials; backend fixes.
- The pre-existing `group_map.html` Django template expression `group.memberships.filter(user=user).exists` is not valid standard Django template syntax; its existing rendering failure needs an independent functional fix.
- Existing `connections/group_chat_detail.html` is referenced by a view but missing from the ZIP; existing issue, not introduced here.
- No real authenticated browser or database end-to-end tests were executed.
