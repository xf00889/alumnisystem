# Targeted Source Cleanup — Follow-up Audit (2026-10-10)

## Why this follow-up exists

The initial source ZIP cleanup focused on generated build/runtime material (`venv`, `staticfiles`, bytecode, backups) rather than app-level code. This additional pass explicitly inspected Django modules, HTML templates, and authored CSS/JavaScript. The original and previous cleaned ZIPs remain unchanged.

## Findings

- Django installed applications: **17** project applications in `INSTALLED_APPS`, retained as active (accounts, core, alumni_directory, events, alumni_groups, surveys, announcements, feedback, connections, location_tracking, mentorship, jobs, donations, cms, setup, log_viewer, docs).
- Three unregistered small app directories **`groups/`, `data_consolidation/`, `alumni_web/`** are flagged for review, not deleted: no runtime route/installed app was found, but the dependency-verification management command explicitly recognizes them as local modules, and external uses have not been ruled out.
- Authored static assets inspected: **83** (`50 CSS`, `33 JS`). **4** files had no filename or path references outside themselves; their links/imports were checked against source templates/JS/Python. These four were removed in the updated ZIPs.
- Project templates inspected: **297** template-path HTML files. **13** had neither an explicit template-path nor basename reference in the scanned source, but several are used by framework conventions (e.g., Django Admin or authentication templates), or may be referenced dynamically.
- `templates/account/login_before_redesign.html` was removed as a clearly obsolete, unreferenced predecessor. Other ambiguous templates were retained rather than mass-deleted.
- There are **no exact-byte duplicate authored CSS/JS assets** in this source snapshot. Overlapping CSS/JS functions and old template variants still warrant runtime-backed functional comparison; this pass did not force-merge them.

## Verified source-file deletions (this follow-up only)

| Removed path | Reason |
|---|---|
| `static/css/alumni_directory.css` | No source/reference usage detected; superseded by module-based alumni-directory styling |
| `static/css/officials_slider.css` | No source/reference usage detected; no stylesheet import or asset load references |
| `static/js/availability-checker.js` | No source/reference usage detected; standalone script is not loaded |
| `static/js/education-cascading-dropdowns.js` | No source/reference usage detected; standalone script is not loaded |
| `templates/account/login_before_redesign.html` | Explicitly superseded pre-redesign login template; no references or active view/template usage found |

## Retained template candidates — do not delete based only on static scans

`jobs/templates/admin/jobs/scrapedjob/change_list.html` (Django Admin override); `templates/account/account_inactive.html`, `templates/account/password_reset.html`, `templates/account/signup.html`, `templates/socialaccount/login_cancelled.html` (authentication packages/framework convention); `jobs/templates/jobs/partials/job_card.html`; `templates/alumni_directory/partials/alumni_detail_content.html`; `templates/announcements/announcement_confirm_delete.html` (possible generic DeleteView naming convention); `templates/components/pagination.html`; `templates/mentorship/mentee_dashboard_new.html`; `templates/mentorship/mentor_dashboard_new.html`; `templates/tracer_study/_public_banner.html`.

The remaining items might be dormant, but their external/runtime/dynamic usage was not conclusively excluded. In particular, `*_new.html` variants may represent unfinished features and need owner confirmation or browser tests before deleting.

## Important limitation: external/static/database usage

A zero-source-reference test strongly supports safe deletion of an authored asset under the current source tree, but is not a proof against a hardcoded external URL, database-configured template name, or unpublished integration. Preserve the previous ZIP as a rollback artifact. The built-in Django checks and browser tests were not run successfully because a compatible dependency environment, secrets and database services were not available.

## Validation and original environment

- Deleted resource names were absent from all scanned Python, JS, CSS, HTML, deployment, JSON, and YAML source files (excluding generated reports).
- All retained application source content was copied byte-for-byte from the previous cleaned ZIP; no active route, model, migration, business method or API was changed.
- An archive variant **with the original Windows `venv/` restored** is provided. That virtual environment is machine-specific (Windows/Python 3.13) and is not a replacement for reconstructing a compatible environment on another OS or deployment target.
- The smaller source-only archive still excludes `venv/` and generated `staticfiles/`; both variants require `collectstatic` during deployment.
- Original project preexisting issues remain: `core/tests/test_services.py` syntax error, one unresolved template include, and 12 unresolved static references in the earlier static audit.

## Recommendation

Before any additional backend-module or template deletion, obtain the application's real route/view coverage and run integration tests with the production-equivalent database, data and user permissions. Do not delete all apparently unreferenced templates, signals, migrations, or management commands based on literal searches.
