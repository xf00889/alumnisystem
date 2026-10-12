# Alumni Service Redesign — Verification

Date: October 10, 2026

## Checks executed

| Check | Result |
|---|---|
| Modified HTML templates / context processor | 17 HTML + 1 Python file |
| New alumni CSS syntax (`tinycss2`) | All six new stylesheets passed |
| Django template syntax using installed Django and stubbed third-party template filters | 17 modified templates passed |
| Role-based layout selection for donations/surveys/feedback/security/notifications | Alumni, staff, superuser, coordinator and anonymous: passed |
| Tracer Study anonymous/public vs regular alumni vs admin layout | Passed |
| Feature vendor-script selection by role/namespace | Passed |
| Original form markup, CSRF tags, route references, input IDs and frontend hooks | Exact comparison of unchanged HTML templates passed |
| Staff/admin Django base template | Byte-for-byte unchanged |
| Staff donation and survey templates excluding their shared base | Byte-for-byte unchanged |
| New static asset references | All local references checked, present |
| CSS, role, static, template and isolation checks | 216 passed, 0 failed |
| Archive integrity and source parity | Verified after packaging |

## Not executed

- Django management `check` / full application startup with the full production dependency set, because the Linux runtime does not have the project-specific stack and database services configured.
- Authenticated end-to-end navigation, donation/GCash submission, conditional survey response, tracer eligibility, feedback editing, notification read state, or responsive browser screenshots.

## Important deployment smoke tests

1. Log in as a regular alumni user: open Donations browse/detail/donation/history/payment instructions/upload; take a survey and complete a tracer study; submit/view/update feedback; open Security and Notifications.
2. Test the payment process in a safe sandbox/demo flow, preserving GCash proof upload, reCAPTCHA, and error validation; **do not send money** as part of a test.
3. Verify survey conditional questions, required field validation, textarea and select values, CSRF and saving, and already-submitted states.
4. Verify an anonymous public visitor on the tracer index, employer study and minimal donation form retains the original public presentation.
5. Verify staff, coordinator and superuser dashboards, Donations verification/managers, Survey admin, Feedback admin and tracer reports remain unaffected.
6. Test at desktop/tablet/mobile sizes with keyboard-only navigation; check bootstrap modals/accordions, browser console errors, and missing CSS requests.
7. Run `python manage.py check` and existing application tests in the correctly configured local environment.

Do not claim production readiness based solely on the static verification above.
