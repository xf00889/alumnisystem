# Deep cleanup validation — 10 October 2026

## Executed tests

| Test | Result |
|---|---|
| Full authored frontend asset filename/path reference scan | PASS (47 CSS and 31 JS retained with at least one source reference) |
| Deleted module import/URL source scan | PASS (no active source imports or URL registration detected) |
| Deleted template references across retained source | PASS (no exact template filename references) |
| CSS orphan block removal | PASS (only named retired page blocks removed) |
| Python syntax compilation | 537/538 source files passed |
| JavaScript `node --check` | 31/31 passed (29 root + 2 app-owned) |
| CSS `tinycss2` parsing | 47/47 passed (45 root + 2 app-owned) |
| Django template literal include/extends path scan | 247 references checked; 1 unresolved |
| Django static literal target scan | 298 references checked; 5 unresolved (app-owned static and Django admin handled) |
| Active code preservation | 3 limited asset/dependency-whitelist edits; other retained source byte-preserved |

### Python errors

- `core/tests/test_services.py`: invalid syntax (test_services.py, line 4)

### Template include/extends unresolved

- `surveys/templates/surveys/admin/report_detail_modal.html` -> `surveys/admin/report_detail_content.html`

### Static references unresolved

- `donations/templates/donations/campaign_form.html` -> `css/flatpickr.min.css`
- `donations/templates/donations/campaign_form.html` -> `js/flatpickr.min.js`
- `templates/accounts/skill_matching.html` -> `js/skill_matching.js`
- `templates/donations/campaign_list.html` -> `images/campaign-placeholder.jpg`
- `jobs/templates/jobs/manage_applications.html` -> `css/job_applications.css`

## Not verified

- Django `manage.py check`, migration checks, and production-dependent service integration; required packages/services are unavailable.
- Browser snapshots, authenticated multi-role page navigation, server-rendered forms, background jobs, third-party and database-driven template references.
- External integration references to removed scaffold namespace names.

Static source scans cannot certify production readiness. Restore from the preceding version if an external integration relies on any retired scaffold/template.
