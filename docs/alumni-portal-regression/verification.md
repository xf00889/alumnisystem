# Alumni Portal — Verification Report

Date: 2026-10-10

| Executed check | Result |
|---|---|
| 58 alumni-related Django template parses (real Django Engine; custom third-party tags/filters stubbed) | 58/58 passed |
| CSS syntax (`tinycss2`, all authored `.css` under project) | 67/67 passed |
| JavaScript syntax (`node --check`, all authored `.js`) | 32/32 passed |
| Python syntax (`ast.parse`) | 538/539 passed; pre-existing malformed `core/tests/test_services.py`, line 4 |
| Constant local alumni template references | No missing references found |
| Local static references from audited alumni templates | 230/231 present; `js/skill_matching.js` missing in baseline |
| Synthetic role/context checks across 6 roles × 10 namespaces | 180 assertions passed |
| Committed Python role-isolation test | 1 unittest case passed, 72 role/app subcases; four assertions per subcase |
| Two-group template-generated map JS syntax | Passed (`node --check` with synthetic marker data) |
| Chromium mobile navigation smoke (fixture, simulated Bootstrap) | Passed (open / Escape / outside click / aria labels) |
| Chromium desktop navigation smoke (fixture) | Passed |
| ZIP integrity | Validated after packaging |
| Source parity with bundled-venv edition | Verified after packaging |

Not run: live Django app, `manage.py check`, full Django tests, authenticated page screenshots, database-backed workflows, actual Bootstrap/CDN loading in production, functional map API, payments, scheduled tasks, or messaging transport. These require the real environment. The parser check verifies syntax, not complete rendering or runtime behavior.
