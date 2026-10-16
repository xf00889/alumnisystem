"""Static checks for User Management UI wiring; no Django database required."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class UserManagementUIContracts(unittest.TestCase):
    def test_account_type_contains_supported_roles_and_campus_field(self):
        form = (ROOT / 'core/forms/user_management_forms.py').read_text()
        for role in ('alumni', 'mentor', 'hr', 'alumni_coordinator', 'admin', 'superuser'):
            self.assertIn(f"('{role}',", form)
        self.assertIn('coordinator_campuses', form)
        self.assertIn('Select at least one campus', form)

    def test_status_modal_is_shared_and_requires_reason(self):
        modal = (ROOT / 'templates/admin/user_management/components/status_confirmation_modal.html').read_text()
        self.assertIn('statusChangeReason', modal)
        self.assertIn('required maxlength="1000"', modal)
        for path in ('user_list.html', 'user_detail.html'):
            template = (ROOT / 'templates/admin/user_management' / path).read_text()
            self.assertIn('components/status_confirmation_modal.html', template)
            self.assertIn('user-status-modal.css', template)

    def test_status_javascript_uses_no_native_alerts_or_missing_campuses(self):
        script = (ROOT / 'static/js/user_management.js').read_text()
        self.assertNotIn('confirm(', script)
        self.assertNotIn('prompt(', script)
        self.assertNotIn('alert(', script)
        self.assertIn('new URLSearchParams', script)
        self.assertIn('JSON.stringify({ action: statusDialog.action, reason })', script)
        self.assertIn('campuses: campuses', script)  # Role action only

    def test_server_requires_reasons_for_single_and_bulk_actions(self):
        view = (ROOT / 'core/view_handlers/user_management_views.py').read_text()
        self.assertIn("'Enter a reason (1–1000 characters) for this status change.'", view)
        self.assertIn("'Enter a reason (1–1000 characters) for this bulk status change.'", view)
        self.assertIn('campus_codes=form.cleaned_data.get', view)

if __name__ == '__main__':
    unittest.main()
