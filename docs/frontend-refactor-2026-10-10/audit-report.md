# Frontend Asset Audit and Refactoring Report

**Date:** October 10, 2026  
**Project:** NORSU Alumni System (Django)  
**Source:** `alumnisystem_gpt.zip`, original project preserved in the delivery ZIP  
**Status:** Static-level refactoring completed; runtime/browser acceptance remains necessary.

## 1. Project inspection

The ZIP contains a Windows Python virtual environment, staticfiles build output, media files, archives and the Django source tree. The authoritative asset changes are in the project's `static/` source tree and Django app/root template directories, not in generated `staticfiles/` or vendor code. The source archive contains existing `.env` files and media; handle the ZIP as sensitive. No secret values are reproduced in this report.

**Template coverage:** 293 HTML templates: 200 root templates plus 93 app-owned templates. Existing authored assets initially included 22 `.css` and 19 `.js` files under `static/` (excluding image/map/build artifacts). Embedded CSS and JS across application templates were also reviewed. Ancillary docs/tests and compiled `staticfiles` were not treated as production template sources.

### Modules and outcomes

| Module/template owner | HTML templates | CSS blocks extracted | JS blocks extracted |
|---|---:|---:|---:|
| `account` | 9 | 3 | 0 |
| `accounts` | 23 | 9 | 5 |
| `accounts-app` | 1 | 0 | 0 |
| `admin` | 17 | 13 | 4 |
| `alumni-directory` | 7 | 3 | 1 |
| `alumni-groups` | 16 | 11 | 3 |
| `announcements` | 9 | 6 | 2 |
| `cms-app` | 30 | 23 | 10 |
| `components` | 11 | 0 | 0 |
| `connections` | 10 | 4 | 0 |
| `core` | 3 | 2 | 0 |
| `core-app` | 1 | 0 | 0 |
| `donations` | 10 | 8 | 0 |
| `donations-app` | 25 | 14 | 3 |
| `emails` | 11 | 0 | 0 |
| `events` | 9 | 5 | 1 |
| `feedback` | 6 | 5 | 1 |
| `jobs` | 3 | 1 | 0 |
| `jobs-app` | 15 | 8 | 0 |
| `landing` | 5 | 0 | 1 |
| `layouts` | 2 | 2 | 0 |
| `legal` | 1 | 0 | 0 |
| `location_tracking-app` | 1 | 0 | 0 |
| `log_viewer-app` | 6 | 4 | 0 |
| `mentorship` | 10 | 4 | 0 |
| `mentorship-app` | 6 | 2 | 0 |
| `setup-app` | 4 | 1 | 0 |
| `socialaccount` | 4 | 3 | 0 |
| `surveys` | 7 | 7 | 0 |
| `surveys-app` | 4 | 2 | 0 |
| `system` | 17 | 13 | 1 |
| `tracer-study` | 10 | 3 | 1 |


## 2. Findings

- **Scattered template-local styles:** Modules such as Alumni Groups, CMS, Accounts, Donations, Surveys and Admin contained sizeable inline CSS. Most styles could be relocated without changing declarations. Page-level root classes now isolate selectors within consolidated module stylesheets.
- **Shared responsibilities scattered across script tags:** Template JS often initializes on DOM ready. 33 safe single-block initializers now live in shared module files, selected by their template marker and an execution-once registry. The identical batch-year validation used by two Alumni Groups creation pages has one shared implementation.
- **High-risk dynamic scripts:** Django expressions, HTML inline-handler functions, multi-script sequencing and deeply nested dashboard implementations are deliberately retained. Moving them without browser testing could break AJAX, validation or global functions.
- **Conflicting CSS keyframe names:** Selectors containing potentially conflicting animation declarations have been left in their templates pending an animation-by-animation review.
- **Duplicated template names under `templates/` and `<app>/templates/`:** Both locations were audited. App-owned templates use dedicated `*-app` bundles to avoid accidentally conflating a project-level override with an app fallback.
- **Potentially obsolete backup/test files:** The project includes legacy templates and backups. No template file was deleted without reliable route/dynamic render evidence; deletion requires a separate usage audit.
- **Generated copies:** `staticfiles/` contains collected/static build artifacts, not edited during this source refactor; a deployment `collectstatic` run is required.

## 3. Implementation

- **CSS blocks moved:** 156 into 26 module/layout CSS files.
- **JS blocks moved:** 33 into 12 guarded module scripts.
- **Total unique templates changed:** 168.
- **Existing source templates removed:** 0; **existing authored CSS/JS source files removed:** 0. Static orphan deletion was not substantiated sufficiently to be safe.
- **Backend controllers, views, routes, models and schemas changed:** 0.
- **Page-gating:** Each changed page adds a small root-class marker before loading a stylesheet or shared script. The original execution point of each extracted JS initializer is retained. Global layout styles remain in independent stylesheets, rather than being mixed across public/authenticated layouts.

### Before

```text
templates/<module>/*.html           # Large per-page <style> and <script> blocks
<app>/templates/<app>/*.html       # Additional embedded CSS/JS outside root templates
static/css/*.css                  # Existing shared and component assets
static/js/*.js                    # Existing shared and component assets
staticfiles/                       # Generated collected assets
```

### After

```text
static/css/modules/
    layout-authenticated.css
    layout-public.css
    accounts.css, alumni-groups.css, donations.css, events.css, ...
    cms-app.css, donations-app.css, jobs-app.css, surveys-app.css, ...
static/js/modules/
    accounts.js, alumni-groups.js, announcements.js, events.js, ...
    cms-app.js, donations-app.js, ...
templates/<module>/*.html
    # Scoping marker + module stylesheet and/or module script reference
<app>/templates/<app>/*.html
    # Corresponding app-specific scoping marker/reference
```

## 4. Validations performed

- **CSS extraction source mappings checked:** 156 passed.
- **CSS module parse passed:** 26 passed.
- **JS extraction source mappings checked:** 33 passed.
- **JS module parse passed:** 12 passed.
- **new asset references verified:** 170 passed.
- **templates token-mapped:** 293 passed.


**Static validation errors:** 0. `node --check` was used for emitted JavaScript. `tinycss2` parsed new CSS. Django 5.0.2's lexer was run against before/after templates to verify that Django tag/variable logic was retained (ignoring newly added static asset tags). Generated file references were checked for existence. The full Django app was **not** started and business logic tests, browser visual comparisons, database migrations, and end-to-end functional flows were **not** executed.

## 5. Known limits and required acceptance checks

1. The new page CSS selectors rely on a small inline JavaScript class marker, so styles from these new bundles require JavaScript to run. Test any environments where CSP or disabled JS may block it.
2. Load representative forms, lists, modals and dashboards under every major module; validate mobile responsiveness, visual parity, and event listeners. In particular test Donations, CMS, Accounts, Alumni Groups and surveys.
3. Test templates where child layout overrides use `{{ block.super }}` and ensure the inherited styles appear in the intended cascade order.
4. Verify full user journeys under an authenticated browser: CRUD, API/fetch, CSRF forms, modals, notifications, messaging, pagination, filters and document upload.
5. Re-run `python manage.py collectstatic --noinput` in the project's deployment environment, then run `python manage.py check` and the existing test suite. Do not distribute this archive publicly without removing original secret and media data.
6. Dynamic template references, backups and complex inline scripts remain **Review** items rather than blindly deleted files. See `asset-inventory.csv` and `app-template-inventory.csv` for detailed decisions.

## 6. Change summaries

- Root-template CSS and JS consolidated with page-level isolation.
- App-owned templates located and consolidated where no Django or global-function dependency blocked safe extraction.
- Existing static JS/CSS references and backend contracts deliberately untouched.
- No broad rewrite, dependency installation, third-party vendor deletion or markup redesign.

This is a source-level refactoring with static checks, **not a claim of full production readiness**.
