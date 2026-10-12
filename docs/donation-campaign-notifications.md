# Public Campaign Navigation & Donor Email Notifications

## Source of truth
`alumnisystem_public_donation_journey_refined.zip` (latest previously generated project archive).

## Implemented

1. **Public campaign browse destination**: Anonymous requests to `/donations/campaigns/` now redirect to `/donations/campaigns/public/`, preserving filters. The new guest page inherits `base_landingpage.html` (university masthead/footer). It lists only public, active, accepting-donations campaigns within their available dates. Authenticated alumni and management keep the original campaign-list view.
2. **Guest links**: Public donation form, progress heading, sidebar, and guest donation status links point directly to the public campaign listing. Existing links to `/donations/campaigns/` for logged-out visitors safely redirect too.
3. **Mandatory guest email**: `DonationForm` requires and validates an email address at form and backend level, including anonymous donor submissions. The email is private and used for recovery/status messages. An authenticated donor's registered email remains the primary recipient, falling back to any recorded donation email.
4. **Administrative verification notifications**: Donation `pre_save` detects status transitions and `post_save` schedules notifications via `transaction.on_commit`. This covers model saves initiated by Django Admin, staff verification, bulk verification, and managed status edits. After proof upload, a proof-received acknowledgement is queued; after `completed`/`failed`/`disputed`/`refunded` or other real transitions, a status update is queued; on completion, an official receipt is also attempted. No message is sent for an unchanged status or an initial unpaid donation.
5. **Email privacy**: Internal staff verification notes were removed from donor-facing emails. The signal resolves current DB state before delivery so callbacks for superseded intermediate states can be skipped. Missing contact details and provider failures are logged; the database transaction is not rolled back due to email failure.

## Change boundaries
No database migrations, changes to payment processing, bypass of CSRF, or removal of staff permission checks. Existing Django Admin pages and authenticated alumni campaign design remain intact.

## Checks actually run
- Python AST parsing: 6 changed/new Python source files **passed**.
- CSS parser: 50 rules **passed**.
- Django template tag-balance checks on affected new/guest templates **passed** (not full Django compilation).
- Chromium isolated responsive HTML/CSS fixture: 320px, 390px, 768px, 1440px **passed**, no horizontal overflow.
- Isolated signal simulation: status, proof, receipt, unchanged, stale update, missing email **passed**. Isolated recipient utility simulation: guest, member, fallback **passed**.
- ZIP integrity and changed/unmodified file inventory **passed**.

**Django integration suite NOT executed here.** Django isn't installed in this execution environment and external package installation failed. Test modules were added but require running in the user's installed application environment. **Actual email delivery NOT verified** (no SMTP/Brevo account connection). Existing project logs state it used the console backend for development, which prints mail instead of sending externally.

## Local acceptance commands
Run in your activated local `.venv`, from the `alumnisystem_gpt` directory:

```powershell
python manage.py check
python manage.py test donations.tests_notifications
python manage.py test donations.tests_payment_flow donations.tests_cancellation
python manage.py runserver
```

Then verify in a private browser session:
1. Visit `/donations/campaigns/`, verify guest redirect to `/donations/campaigns/public/`, and ensure no private/draft campaigns appear.
2. Submit a public donation with blank and malformed email: form should refuse; with a valid email proceed to payment instructions.
3. Submit proof of a test GCash transaction; verify that it changes to pending verification, and that the donor receives a proof-received notice (in console logs while using console backend).
4. With a staff account, mark the test donation `completed`, `failed`, or `disputed` via verification UI / Django Admin and check donor email logs/delivery. Completing a verified donation should also attempt a receipt email. Save without status change and verify no new status email.
5. Configure SMTP or Brevo in development/staging if **real external emails** are required. Do not expect inbox delivery from `django.core.mail.backends.console.EmailBackend`. Inspect provider logs for failures.

## Operational limitations
- After-commit callbacks and logging improve correctness, but **email delivery is best-effort**, not a durable outbox. Delivery can fail after DB commit during provider outages. A background queue/outbox with retries would be needed for guaranteed retryability.
- Legacy donations with no usable email cannot receive notifications; administrative logs warn about missing address. The new required field affects new public guest submissions, not legacy records.
- No live SMTP/Brevo verification or database-backed end-to-end browser test was possible in this environment.
