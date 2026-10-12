# Django Alumni System — Project Cleanup Audit

**Date:** 2026-10-10  
**Input:** `alumnisystem_refactored_2026-10-10(1).zip` (preserved unchanged)  
**Method:** Full ZIP member inventory; Django app and URL inspection; source import/reference searches; compiled-code and generated asset classification; conservative data preservation.

## 1. Files, directories and modules

- Original ZIP: **28,196 files**, **5,968 logical directories**, **501.42 MB uncompressed**, **203.26 MB on disk**.
- Source-like files inspected for references: **1,065** (non-runtime generated files).
- Python source files retained: **550**.
- Active Django apps from settings: **accounts, core, alumni_directory, events, alumni_groups, surveys, announcements, feedback, connections, location_tracking, mentorship, jobs, donations, cms, setup, log_viewer, docs**.
- Existing frontend refactor module stylesheets/scripts retained; no CSS/JS rewrite performed during this cleanup.

## 2. Implemented SAFE TO DELETE categories

| Category | Files removed | Raw size (MB) | ZIP member compressed size (MB) | Evidence |
|---|---:|---:|---:|---|
| `venv` | 24,794 | 383.05 | 121.06 | Local Windows virtual environment |
| `staticfiles` | 1,148 | 9.98 | 5.66 | Regenerable Django collectstatic output |
| `pycache` | 499 | 3.87 | 1.66 | Compiled Python bytecode |
| `archive` | 336 | 0.97 | 0.25 | Archived backups and tool caches |
| `scraper_debug` | 11 | 22.30 | 6.26 | Historical scraper debug snapshots |
| `root_tmp` | 11 | 0.09 | 0.02 | Root scratch/debug artifacts |
| `backup` | 7 | 1.24 | 0.20 | Obsolete backup copies |
| `legacy_template` | 4 | 2.56 | 0.40 | Unreferenced legacy dashboard/login templates |
| `pip_output` | 2 | 0.00 | 0.00 | Accidental pip console output |
| `empty_db` | 1 | 0.00 | 0.00 | Empty test database |

For **every deleted path**, see `deleted-resources.csv`; for all original paths and classifications, see `cleanup-inventory.csv`.

### Reasoning

- `venv/`: OS-specific local environment is not portable or appropriate in deployment source; `requirements.txt`, `build.sh`, `render.yaml` preserve dependency recreation. Re-create an environment before local execution.
- `staticfiles/`: generated Django static collection, confirmed by `STATIC_ROOT`, `STATICFILES_DIRS`, Render build command and `build.sh`. Re-run `collectstatic` after dependency installation. The previous collected snapshot was stale relative to newly extracted module files.
- Bytecode, test caches, historic archived backups, playwright captures and named scratch files are generated, ignored, or explicitly placed outside active Django paths.
- Obsolete backup copies and four unreferenced backup/original/fixed HTML templates were verified against literal render/include/extends references. Canonical files retained; active `events/event_list_new.html` and other possibly work-in-progress variants are untouched. Root temporary names were searched before removal.
- `media/scraper_debug/` contains HTML snapshots named `selenium_debug_*` and `bossjob_debug_*`, with no static application references; all other `media/` documents and uploads retained. **Note:** external links or undocumented manual uses of debug snapshots cannot be ruled out; recover from the unchanged original ZIP if needed.

## 3. MUST KEEP — retained

- All Django `INSTALLED_APPS` and registered URL modules; views, services, templates, forms, models, migrations and background/management commands.
- Existing module CSS/JS, Django app-local static assets and tests. **18 existing empty directory entries** (e.g. future media/static/template storage paths) are preserved because runtime purpose cannot be ruled out.
- `requirements.txt`, `.gitignore`, `render.yaml`, `build.sh`, `start.sh`, configuration and environment files.
- `media/` uploads, proof of payments, documents, images and `media/logs/archives/` audit evidence, excluding the 11 identified debug snapshots.
- **`logs/` is retained**, despite being ignored by Git: `log_viewer/views.py` explicitly reads historical `alumni_system.log` and `errors.log`; deleting would remove visible operational log history.
- Documentation and dev/testing commands not proven obsolete.

## 4. REQUIRES REVIEW — retained

- `groups/`, `data_consolidation/`, and `alumni_web/`: not present in `INSTALLED_APPS`; no proof that maintenance commands, external scripts or planned integrations will not use them. No deletion.
- Some historical/overlapping frontend static assets and template variants: dynamic-use evidence insufficient. Unreferenced `*_new.html` variants retained unless conclusively obsolete; four clearly labeled legacy variants removed.
- Dependency list: **zero dependencies removed**. A missing direct import is insufficient to prove unused under Django auto-discovery, transitive imports and operational scripts. Audit package usage in a matching Windows environment and production Linux build before editing versions.
- Potential duplicate user uploads: media file naming or equal size is not evidence of database unreferenced status. Preserved.
- Environment files (`.env`, `.env.production`) may contain credentials; retained to avoid breaking local config; treat the ZIP as sensitive.

## 5. Duplicate implementations

- Verified obsolete backup copies and archived alternate scripts removed. No active backend implementations were merged: behavioral equivalence could not be proved from static analysis alone.
- Newly consolidated `static/css/modules/*` and `static/js/modules/*` remain the preferred frontend assets; old active CSS/JS was not removed on filename resemblance alone.

## 6. Validation and limitations

See `verification.md` for commands, checks, and known limitations. Syntax checks: 33 JS and 50 CSS files passed; one existing Python test file (`core/tests/test_services.py`) has a syntax error. One template include and 12 static resource paths remain unresolved in the static scan; they need checking in the running Django environment. Core application tests, production DB, external APIs, scheduled jobs and browser tests require a complete running environment and were not demonstrated here. Source logic and active HTML/CSS/JS were preserved at the byte level.

## 7. Recommendations

1. Make a separate deployment that runs `pip install -r requirements.txt`, `collectstatic`, `check`, migrations and tests with your actual environment configuration before promotion.
2. Verify package names/versions on the target Python 3.11 environment, since the removed local venv was Windows Python 3.13.
3. Inspect inactive-app candidates and any dynamically named frontend asset references before additional deletion.
4. Use the built-in log retention/archive controls rather than manually purging `logs/` or `media/logs/archives/`.
5. Stop distributing live credentials and private uploaded media in source ZIPs when transitioning to a public repository.
