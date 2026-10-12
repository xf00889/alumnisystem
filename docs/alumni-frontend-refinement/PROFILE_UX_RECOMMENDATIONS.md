# Suggested UX direction — Alumni Profile

1. **Profile detail = read-only overview** with a single prominent **Edit profile** action; details may remain organized in view-only tabs, but there should be no competing add/edit modals.
2. **Edit profile = one editing workspace.** Personal, Education, Experience, Skills and Documents are persistent sections; clearly distinguish **Saved**, **Unsaved**, and **Needs attention** states.
3. **Save this section** validates only that section. **Save & Next** makes progress predictable. Finishing is not blocked by unrelated optional sections; required account data retains backend validation.
4. **Progress indicator:** later add an accurate completeness indicator calculated from actual saved fields, not arbitrary step count. The account owner should know precisely which information is missing.
5. **Do not silently autosave incomplete documents or file uploads.** Manual section saves plus an unsaved-change warning are safer until versioned drafts, upload cleanup and conflict handling are implemented.
6. **Career path and achievements:** migrate remaining edit/add/delete actions to the editor before deleting legacy flows. Treat them as dedicated subsections rather than using the profile-detail view as a second editor.
7. **Privacy:** mark public/private fields and document visibility clearly; preserve owner-based authorization, server validation, audit logging and POST-only deletion.
8. **Next test pass:** authenticated browser tests for admin and regular alumni, submit each formset, refresh and resume, document replacement/removal, CSRF expiry, two-tab unsaved changes, 320px mobile, and keyboard-only navigation.
