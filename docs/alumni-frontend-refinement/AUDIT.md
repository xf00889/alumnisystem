# Alumni frontend refinement — screenshot audit

Baseline: **alumnisystem_gpt(1).zip** (provided by the user). The original archive is unchanged.

## Implemented alumni-only UI corrections

- **Job Board:** hide redundant desktop and mobile job-count chips for alumni; preserve filter and sort parameters and admin counts.
- **Job Details:** flatten decorative nested cards in the metadata, description, and other content sections while retaining the actual job text and application actions.
- **Conversations:** use one New Message dropdown with Direct Message and Create Group. Remove the redundant empty-state View My Connections button only on alumni pages.
- **Fundraising:** add an alumni breadcrumb and align the campaign filter panel with the Job Board's input sizing, labels, padding, and card treatment.
- **Surveys:** add breadcrumb, normalize page-header spacing, card widths, statistics grid, search/filter area, and mobile layout.
- **Notifications:** add breadcrumb and align header and content gutters.
- **Edit Profile:** align the hero width with page content, correct Change Picture button contrast, add five tab controls, section-specific Save and Save & Next, and a status/validation summary.
- **Profile detail:** replace main add/edit modal entry buttons for skills, education, experience, and documents with links to the unified editor for regular alumni. Existing staff controls remain.

## Saved-section behavior

`accounts:save_profile_section` (POST-only; login-protected; CSRF) validates **only** the selected section (`personal`, `education`, `experience`, `skills`, `documents`). A successful save persists that section and reloads the editor so new formset rows receive actual database IDs. Other sections are not overwritten. Unfinished **other sections** can be completed later. Invalid fields inside the current section are not stored as a draft.

The document deletion operation is accessible inside the editor and requires POST; old management endpoints remain available for legacy staff flows. A success banner is shown after a section save; attempted navigation away with unsaved inputs warns the user.

## Scope and constraints

This is not a redesign of backend services or all admin interfaces. The read-only profile detail tabs remain useful for presenting existing data, but editing is centralized for the five supported sections. Some career-path and achievement actions are legacy integrations and are not yet fully migrated into the new editor; these must be audited before deleting their forms/endpoints. No new Django database migration was introduced.

For true *field-level unfinished drafts* (e.g., saving a half-entered required phone number across devices), a separate user-owned draft model with an expiry/cleanup policy and server-side validation on publication is recommended; the present implementation saves fully valid individual sections, **not** invalid within-section drafts.

Accessibility: profile tab controls implement tablist/selected states, keyboard navigation, aria-live save status and server-validation messaging. Mobile styling is responsive; a final integrated browser and database test is still needed.
