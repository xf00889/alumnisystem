"""Regression coverage for creating limited HR users via administration User Management."""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models.user_management import UserAuditLog
from core.services.user_management import UserManagementService
from jobs.hr_access import is_hr_only


@override_settings(
    SECURE_SSL_REDIRECT=False,
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage',
    STORAGES={
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    },
)
class AdminHRAccountCreationTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_guard = patch('setup.middleware.SetupRequiredMiddleware._is_setup_complete', return_value=True)
        setup_guard.start()
        cls.addClassCleanup(setup_guard.stop)

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.owner = User.objects.create_superuser(
            username='hr-creation-owner', email='hr-owner@example.org', password='StrongAdminPass!2026'
        )
        cls.staff = User.objects.create_user(
            username='hr-creation-staff', email='staff-owner@example.org', password='StrongAdminPass!2026', is_staff=True
        )

    def post_data(self, **overrides):
        result = {
            'email': 'new-hr@example.org',
            'first_name': 'Career',
            'last_name': 'Manager',
            'account_type': 'hr',
            'password': 'InitialHrPassword!2026',
            'password_confirm': 'InitialHrPassword!2026',
        }
        result.update(overrides)
        return result

    def test_admin_can_open_preselected_hr_creation_form(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('core:user_create') + '?account_type=hr')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form']['account_type'].value(), 'hr')
        self.assertContains(response, 'Restricted HR access')

    def test_hr_creation_is_limited_audited_and_visible_in_user_management(self):
        self.client.force_login(self.owner)
        with patch('core.services.user_management.send_email_with_provider') as mail:
            response = self.client.post(reverse('core:user_create'), self.post_data(send_welcome_email='on'))
        self.assertEqual(response.status_code, 302)
        new_hr = get_user_model().objects.get(email='new-hr@example.org')
        self.assertTrue(new_hr.check_password('InitialHrPassword!2026'))
        self.assertTrue(is_hr_only(new_hr))
        self.assertTrue(new_hr.profile.is_hr)
        self.assertFalse(new_hr.profile.is_alumni_coordinator)
        self.assertFalse(new_hr.is_staff)
        self.assertFalse(new_hr.is_superuser)
        self.assertTrue(UserAuditLog.objects.filter(user=new_hr, performed_by=self.owner, action='ROLE_ASSIGN', details__role='hr').exists())
        mail.assert_called_once()
        sent = mail.call_args.kwargs
        self.assertEqual(sent['recipient_list'], ['new-hr@example.org'])
        self.assertNotIn('InitialHrPassword!2026', sent['message'])
        self.assertEqual(sent['html_message'], None)
        filtered = self.client.get(reverse('core:user_list'), {'role': 'hr'})
        self.assertEqual(filtered.status_code, 200)
        self.assertContains(filtered, 'new-hr@example.org')

    def test_normal_user_option_does_not_gain_hr_or_staff_rights(self):
        self.client.force_login(self.owner)
        result = self.client.post(reverse('core:user_create'), self.post_data(account_type='standard'))
        self.assertEqual(result.status_code, 302)
        user = get_user_model().objects.get(email='new-hr@example.org')
        self.assertFalse(user.profile.is_hr)
        self.assertFalse(user.is_staff)

    def test_unauthorized_staff_cannot_create_hr_account(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse('core:user_create'), self.post_data())
        self.assertNotEqual(response.status_code, 200)
        self.assertFalse(get_user_model().objects.filter(email='new-hr@example.org').exists())

    def test_form_rejects_forged_privileged_role(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse('core:user_create'), self.post_data(account_type='superuser'))
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'account_type', 'Select a valid choice. superuser is not one of the available choices.')
        self.assertFalse(get_user_model().objects.filter(email='new-hr@example.org').exists())

    def test_service_rejects_role_escalation_and_invalid_types(self):
        result = UserManagementService.create_user(
            email='new-hr@example.org', first_name='Career', last_name='Manager',
            password='InitialHrPassword!2026', created_by=self.staff,
            send_email=False, account_type='hr',
        )
        self.assertFalse(result[2])
        result = UserManagementService.create_user(
            email='new-hr@example.org', first_name='Career', last_name='Manager',
            password='InitialHrPassword!2026', created_by=self.owner,
            send_email=False, account_type='superuser',
        )
        self.assertFalse(result[2])
        self.assertFalse(get_user_model().objects.filter(email='new-hr@example.org').exists())
