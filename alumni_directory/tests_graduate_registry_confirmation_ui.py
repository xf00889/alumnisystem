"""Protect the Graduate Registry page structure and explicit import confirmation."""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(MIDDLEWARE=[mw for mw in settings.MIDDLEWARE if mw != 'setup.middleware.SetupRequiredMiddleware'])
class RegistryConfirmationUITests(TestCase):
    def setUp(self):
        admin = get_user_model().objects.create_superuser(
            username='registry_confirm_admin', email='confirm_ui@example.com', password='pw'
        )
        self.client.force_login(admin)

    def test_import_precedes_registry_table_and_confirmation_precedes_difference_rows(self):
        response = self.client.get(reverse('alumni_directory:graduate_registry'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertLess(content.index('id="registry-compare"'), content.index('id="registry-list"'))
        self.assertLess(content.index('id="grComparisonMetrics"'), content.index('id="grConfirmCheckbox"'))
        self.assertLess(content.index('id="grConfirmCheckbox"'), content.index('id="grComparisonTablePanel"'))

    def test_separate_confirmation_busy_success_error_dialogs_exist(self):
        response = self.client.get(reverse('alumni_directory:graduate_registry'))
        for dialog_id in ('grConfirmDialog', 'grBusyDialog', 'grFeedbackDialog'):
            self.assertContains(response, f'id="{dialog_id}"')
        for button_id in ('grConfirmCancel', 'grConfirmProceed', 'grCommitButton'):
            self.assertContains(response, f'id="{button_id}"')
        self.assertContains(response, 'Confirm registrar import?')

    def test_upload_field_helper_text_removed_but_approval_notice_remains(self):
        response = self.client.get(reverse('alumni_directory:graduate_registry'))
        for old_text in (
            'Maximum 10 MB. Original registrar files',
            'If a list does not identify campuses',
            'Only used when a year cannot be identified',
        ):
            self.assertNotContains(response, old_text)
        self.assertContains(response, 'approved by the registrar before importing')
