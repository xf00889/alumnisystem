# Changelog — deep cleanup 2026-10-10

- Removed 3 unregistered Django scaffold module directories, totaling 12 source files.
- Removed 8 obsolete or unreferenced templates, preserving framework-convention templates and all active routes.
- Pruned 2 orphan template-specific CSS sections from shared module stylesheets.
- Updated dependency verification whitelist to reflect removed scaffold modules.
- Preserved active `alumni_groups/` and all other registered Django apps, their migrations, models, views, static assets, and database requirements.
- Kept possible runtime-generated CSS/JS references in place for browser regression testing.
- Removed `static/css/availability-checker.css` after confirming its only previously related JS was already retired and no source loads it.
