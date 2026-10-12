# Cleanup changelog — 2026-10-10

- Removed **26,813** generated, archived or debug ZIP file entries.
- Removed bundled OS-specific `venv/` and generated `staticfiles/` snapshot.
- Removed compiled caches, obsolete backup copies and four unreferenced legacy HTML templates, old root scratch experiments, and 11 historical scraper-debug snapshots.
- Kept logged events and audit data intact because `log_viewer` reads historical files.
- No active Python, HTML, CSS, JS, database migration, or requirement dependency files changed.
- Added `PROJECT_CLEANUP_README.md` and cleanup audit/verification/inventory files under `docs/project-cleanup-2026-10-10/`.
