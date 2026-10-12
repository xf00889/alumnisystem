# NORSU Alumni System — Donation Proof Integrity and Notification Diagnostics

**Baseline:** Uploaded `alumnisystem_gpt(3).zip` (used unchanged as input).  
**Scope:** Donation proof persistence, donor email logging/preview semantics, and evidence-based fraud alerts.  
**Database schema changes:** None. **UI changes:** None. **Payment provider behavior:** Not changed.

## Root cause: submitted reference number and proof were discarded

In `donations/views.py`, `upload_payment_proof()` previously validated `PaymentProofForm(..., instance=donation)` and *after validation* replaced its model instance with `locked` from `select_for_update()`. Calling `form.save(commit=False)` then saved the freshly loaded instance, without the submitted `reference_number` or `payment_proof`. The status nevertheless advanced to `pending_verification`, explaining the log's `Reference: None` and proofless records.

The view now acquires the row lock **before binding and validating the POST form**, saves the reference and receipt on the same locked record, and only advances the status after the form passes validation. Existing owner/guest access checks, file validation, CSRF middleware, redirect behavior, and fraud screening remain in place.

This change does not retroactively fix records previously saved without receipts. Use the read-only audit command below, review the GCash evidence with staff, and determine whether donors need to resubmit. Never automatically mark these records as paid or generate fake references.

## Email and Windows logging

- Removed Windows-`cp1252` incompatible emoji characters from the donation acknowledgement logging path. Switched to parametrized and less personally identifying messages.
- Prevented a proof-received acknowledgement when no persisted proof/reference exists.
- Added an **opt-in `require_delivery=True`** flag to `core.email_utils.send_email_with_provider()`, used by donation acknowledgement, status and receipt notifications. If SMTP uses Django's development console backend, it still renders the email in the terminal but returns `0` for these donation notifications, meaning **not delivered**. A receipt is not marked `receipt_sent` from a console preview. Existing callers outside donations keep the default behavior.
- Explicit console-preview logging replaces misleading SMTP-delivered wording in the shared helper. Successful SMTP/API backend processing still does not guarantee inbox delivery; configure a real SMTP or Brevo provider and verify recipient inboxes.
- Historical status/receipt emails will display `Not provided` instead of the literal word `None` if older records lack reference data. This is **presentation only**; the audit command identifies the records requiring correction.

## Fraud alerts

- `FraudAlert.__str__()` now displays `Donation #<id>` when a GCash reference is not yet present.
- Removed the rule that treated common rounded donation amounts (such as PHP 100) as inherently suspicious.
- The 24-hour same-amount pattern now counts `pending_verification` or `completed` donations, not abandoned `pending_payment` or `cancelled` intents. Legitimate repeated transactions may still warrant manual review when thresholds are met.
- A receipt storage/read exception is no longer itself returned as evidence of duplicate-image fraud.
- Existing fraud alerts are retained for staff audit; no old records are deleted or relabeled in the database.

## Files changed

| Path | Action |
| --- | --- |
| `donations/views.py` | Rebind and validate proof form on locked row, then persist evidence + status |
| `donations/email_utils.py` | Evidence check, ASCII logging, backend-delivery requirement, safe reference display |
| `donations/signals.py` | Skip invalid proof acknowledgement for evidence-less legacy transitions |
| `donations/models.py` | Informative fraud-alert fallback label |
| `donations/fraud_detection.py` | Exclude unpaid intents and round-amount false positives |
| `core/email_utils.py` | Distinguish console preview from delivery for opt-in callers |
| `donations/tests_proof_integrity.py` | New regression cases (not executable in this environment) |
| `donations/management/commands/audit_donation_proofs.py` | New read-only legacy data integrity audit |

## Verification done here

- Python AST parse and syntax compilation for all eight modified/new Python modules: **passed**.
- Source checks confirm locked form binding precedes validation, no post-validation instance replacement, and status changes occur only on successful form validation: **passed**.
- ZIP integrity and preservation of all unrelated original files: **passed**.
- **Django integration tests could not run:** Django is not installed in this execution environment; pip installation failed because external package index DNS was unavailable. No database, email provider, or live GCash reconciliation was accessed.

## Required local commands

From `alumnisystem_gpt` on your Windows development machine:

```powershell
python manage.py check
python manage.py audit_donation_proofs
python manage.py test donations.tests_proof_integrity donations.tests_payment_flow donations.tests_notifications
python manage.py runserver
```

Repeat a fresh test donation with a valid GCash reference and sample receipt (do not use real customer funds). Verify the `Donation.reference_number` and stored `payment_proof` exist in Django Admin, status is `pending_verification`, and the acknowledgement references the correct transaction. A submitted form without a reference or valid image must retain `pending_payment`.

If the email provider is still the console backend, the terminal output is only a **preview**. Configure a real verified provider in the application's email settings before testing live recipient delivery.

For any legacy missing-evidence donations identified by the audit command, staff should manually reconcile with bank/GCash evidence. Do not approve them based only on a status or receipt email.

**Deployment:** No database migration required. Backup your database and private payment-proof storage before changing a deployed installation. The full ZIP includes potentially sensitive `.env`, media and local runtime files; do not publish it.
