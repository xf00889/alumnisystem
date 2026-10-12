# Deep application-level source cleanup — 10 October 2026

## Scope and conclusions

This pass begins with `alumnisystem_source_cleaned_2026-10-10.zip` (rather than the original pre-refactor project). It specifically targets abandoned Django scaffolding, unreachable templates, and stale CSS blocks. It does **not** remove installed Django apps, models in use, migrations, or dependencies.

- **3 unregistered scaffold directories removed:** `groups/`, `data_consolidation/`, `alumni_web/`.
- **8 unreferenced/retired template files removed**, including two unused mentorship dashboard variants and two explicitly retired copies.
- **21 source files removed** (1,195,123 bytes, before ZIP compression).
- **1 orphaned standalone CSS file removed** (`static/css/availability-checker.css`) after verifying zero source asset-loading references.
- **2 page-scoped CSS blocks removed** from existing module CSS files; styles for active templates retained.
- **1 developer-only dependency verifier whitelist corrected** to avoid classifying removed modules as local.
- **0 active installed apps, active URL mappings, database migrations, dependency manifests or JS files removed.**

The `groups/` scaffolding is distinct from **`alumni_groups/`**, which serves the working Groups feature and remains unchanged.

## Retired template evidence

| Removed | Evidence |
|---|---|
| `templates/mentorship/mentor_dashboard_new.html` | Superseded by the live mentor_dashboard.html rendered in mentorship/views.py; no include/extend/render references |
| `templates/mentorship/mentee_dashboard_new.html` | Superseded by the live mentee_dashboard.html rendered in mentorship/views.py; no include/extend/render references |
| `templates/tracer_study/_public_banner.html` | Unreferenced standalone tracer-study banner partial, no include or render references |
| `templates/components/pagination.html` | Unreferenced pagination partial, no include/render references |
| `templates/alumni_directory/partials/alumni_detail_content.html` | Unreferenced alumni-detail partial, no include/render references |
| `jobs/templates/jobs/partials/job_card.html` | Unreferenced job-card partial; active jobs/views.py renders other named partials |
| `cms/templates/cms/timeline_item_list_backup.html` | Explicit CMS timeline backup; canonical timeline_item_list.html is used by cms/views.py |
| `mentorship/templates/mentorship/messaging/messaging_page_fixed.html` | Alternative fixed messaging template not rendered; mentorship/messaging_views.py renders messaging_page.html |

## Module evidence

- **`groups/`** — Placeholder models, views, and administration; not registered or imported (separate active alumni_groups app preserved)
- **`data_consolidation/`** — Unused generated scaffold without registrations, imports, or routes
- **`alumni_web/`** — Unincluded Coming Soon placeholder URL module; not registered or imported

## CSS and JavaScript audit

All **47 CSS files and 31 JavaScript files** remaining across the root `static/` directory and app-level `static/` directories have source-name references in the scanned project. The `availability-checker.css` file is excluded because no source usage was found and its matching JS file had already been removed in the preceding cleanup. These are **not** safely deletable merely because an individual selector or function name is absent from a literal template search: JavaScript, responsive states, Django forms, imported UI components, and conditional HTML can create selectors dynamically. The two confirmed orphan CSS sections were removed together with their retired template variants. No module JS was removed in this pass.

Function-level and selector-level dead code beyond these confirmed blocks is retained pending page-by-page runtime coverage; no blanket elimination was attempted.

## Files changed or removed

- Entire contents of `groups/`, `data_consolidation/`, and `alumni_web/` (listed individually in deletion CSV).
- `static/css/availability-checker.css`: unused standalone stylesheet.
- The eight template paths detailed above.
- `static/css/modules/cms-app.css`: removed CSS for the obsolete CMS timeline backup.
- `static/css/modules/mentorship-app.css`: removed CSS for the obsolete messaging fixed variant.
- `core/management/commands/verify_dependencies.py`: removed three dead module names from `LOCAL_MODULES` only.

## Retained for safety

Authentication templates (allauth/Django convention), admin overrides, `templates/announcements/announcement_confirm_delete.html` (Django `DeleteView` convention), registered Django apps, migrations, signals, scheduled jobs, security hooks, uploaded user media, and audit logs. Standalone maintenance scripts and potential duplicated application logic were not deleted based on static heuristics alone.

## Limitations

Static source tracing is not exhaustive proof against database-stored template identifiers, third-party plugins, external clients importing a deleted namespace, or manually invoked placeholder functionality. The original ZIP and previous cleaned ZIP remain unchanged and are available for rollback. Full Django startup and authenticated browser regression tests were not possible in this environment; see the verification report.
