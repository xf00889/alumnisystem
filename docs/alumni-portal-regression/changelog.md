# Alumni Portal — Regression Fix Changelog

- Restored the Groups map's active-group list and metadata in its existing Django view without adding database fields or exposing member coordinates.
- Replaced invalid ORM call in a Django template with a membership ID check.
- Prevented repeated JavaScript marker declarations from conflicting when several groups render.
- Escaped group names/descriptions before injection into JavaScript-generated popup markup.
- Added browsable group links, existing campus display, and an honest unavailable-map state for regular alumni, without altering staff/admin presentation.
- Prevented HR-role users (who can manage job postings) from receiving the regular-alumni layout, preserving the legacy administrative presentation.
- Added a dependency-free role-layout regression test (stdlib unittest).
- Documented existing missing Skill Matching JavaScript, missing group map geographic model fields, and an existing malformed backend test. No placeholder services or false feature implementations added.

No filenames use redesign milestone numbers. No admin base template, migrations, payment logic, route definitions, or database models were modified.
