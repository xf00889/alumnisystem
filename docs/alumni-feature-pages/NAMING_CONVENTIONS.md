# Alumni frontend naming conventions

Name implementation files and integration flags by their purpose, not by the development milestone in which they were added.

- Shared alumni feature-page styling: `static/css/alumni/page-foundation.css`
- Alumni breadcrumb component: `templates/alumni/components/breadcrumbs.html`
- Presentation flag: `use_alumni_layout`
- Optional feature-script loading: `load_alumni_feature_scripts`
- Base template selector: `alumni_page_base` (unchanged; already descriptive)
- Alumni foundation documentation: `docs/alumni-portal-foundation/`
- Feature-page documentation: `docs/alumni-feature-pages/`

Keep module CSS named for its module (`profile.css`, `directory.css`, `jobs.css`, `mentorship.css`).

**Compatibility note:** `group_create_phase1` and `group_create_phase2` are existing steps in the alumni group-creation workflow, not names for the frontend-redesign implementation. Their URL names, views and templates are intentionally untouched to avoid breaking existing routes and links.
