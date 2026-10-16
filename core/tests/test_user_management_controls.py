"""Regression tests: initial account roles and audited status changes.

All privileged creation/status endpoints must remain superuser-only. No sample
accounts are inserted into production; Django TestCase creates test records.
"""
import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from alumni_directory.models import Alumni
from core.forms.user_management_forms import UserCreationForm
from core.models.coordinator_campus import CoordinatorCampus
from core.models.user_management import UserStatusChange, UserAuditLog
from core.services.user_management import UserManagementService


@override_settings(
    SECURE_SSL_REDIRECT=False,
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage',
    STORAGES={
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    },
)
class UserManagementControlsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        patcher = patch('setup.middleware.SetupRequiredMiddleware._is_setup_complete', return_value=True)
        patcher.start()
        cls.addClassCleanup(patcher.stop)

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.owner = User.objects.create_superuser(
            username='control-root', email='control-root@example.org', password='TestRootPass!123'
        )
        cls.staff = User.objects.create_user(
            username='control-staff', email='control-staff@example.org', password='TestStaffPass!123', is_staff=True
        )
        cls.member = User.objects.create_user(
            username='control-member', email='control-member@example.org', password='TestMemberPass!123'
        )

    def create_payload(self, role, **extras):
        data = {
            'email': 'new-controls@example.org', 'first_name': 'Created',
            'last_name': 'Account', 'password': 'StrongRolePass!123',
            'password_confirm': 'StrongRolePass!123', 'account_type': role,
        }
        data.update(extras)
        return data

    def test_form_displays_all_supported_initial_roles(self):
        roles = dict(UserCreationForm.ACCOUNT_TYPE_CHOICES)
        for role in ('standard', 'alumni', 'mentor', 'hr', 'alumni_coordinator', 'admin', 'superuser'):
            self.assertIn(role, roles)
        self.assertFalse(UserCreationForm(self.create_payload('alumni_coordinator')).is_valid())

    def test_coordinator_rejects_invalid_or_missing_campuses(self):
        self.client.force_login(self.owner)
        for campuses in ([], ['FAKE']):
            with self.subTest(campuses=campuses):
                response = self.client.post(reverse('core:user_create'), self.create_payload(
                    'alumni_coordinator', coordinator_campuses=campuses
                ))
                self.assertEqual(response.status_code, 200)
                self.assertFalse(get_user_model().objects.filter(email='new-controls@example.org').exists())

    def test_hr_remains_restricted_non_staff(self):
        self.client.force_login(self.owner)
        result = self.client.post(reverse('core:user_create'), self.create_payload('hr'))
        self.assertEqual(result.status_code, 302)
        user = get_user_model().objects.get(email='new-controls@example.org')
        self.assertTrue(user.profile.is_hr)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_coordinator_requires_valid_campus_and_is_nonstaff(self):
        self.client.force_login(self.owner)
        selected = Alumni.CAMPUS_CHOICES[0][0]
        response = self.client.post(reverse('core:user_create'), self.create_payload(
            'alumni_coordinator', coordinator_campuses=[selected]
        ))
        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(email='new-controls@example.org')
        self.assertTrue(user.profile.is_alumni_coordinator)
        self.assertFalse(user.is_staff)
        self.assertEqual(list(CoordinatorCampus.objects.filter(user=user).values_list('campus', flat=True)), [selected])

    def test_staff_cannot_provision_any_elevated_account(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse('core:user_create'), self.create_payload('superuser'))
        self.assertNotEqual(response.status_code, 302)
        self.assertFalse(get_user_model().objects.filter(email='new-controls@example.org').exists())

    def test_admin_and_superuser_roles_set_privileges_with_audit(self):
        for role in ('admin', 'superuser'):
            with self.subTest(role=role):
                user, profile, ok, error = UserManagementService.create_user(
                    email=f'{role}-new@example.org', first_name='Admin', last_name='New',
                    password='StrongRolePass!123', created_by=self.owner,
                    send_email=False, account_type=role,
                )
                self.assertTrue(ok, error)
                self.assertTrue(user.is_staff)
                self.assertEqual(user.is_superuser, role == 'superuser')
                self.assertTrue(UserAuditLog.objects.filter(user=user, action='ROLE_ASSIGN').exists())

    def test_mentor_created_unverified_and_not_available(self):
        user, _, ok, error = UserManagementService.create_user(
            email='mentor-new@example.org', first_name='Mentor', last_name='New',
            password='StrongRolePass!123', created_by=self.owner,
            send_email=False, account_type='mentor',
        )
        self.assertTrue(ok, error)
        self.assertFalse(user.mentor_profile.is_verified)
        self.assertFalse(user.mentor_profile.accepting_mentees)
        self.assertFalse(user.mentor_profile.is_active)

    def test_status_toggle_requires_reason_and_persists_audit(self):
        self.client.force_login(self.owner)
        route = reverse('core:user_status_toggle', args=[self.member.pk])
        invalid = self.client.post(route, data=json.dumps({'action': 'disable', 'reason': ' '}),
                                   content_type='application/json')
        self.assertEqual(invalid.status_code, 400)
        self.member.refresh_from_db()
        self.assertTrue(self.member.is_active)
        with patch('core.services.user_management.send_email_with_provider'):
            valid = self.client.post(route, data=json.dumps({'action': 'disable', 'reason': 'Verified policy violation'}),
                                     content_type='application/json')
        self.assertEqual(valid.status_code, 200, valid.content)
        self.member.refresh_from_db()
        self.assertFalse(self.member.is_active)
        self.assertTrue(UserStatusChange.objects.filter(user=self.member, reason='Verified policy violation', new_status=False).exists())
        self.assertTrue(UserAuditLog.objects.filter(user=self.member, action='STATUS_DISABLE').exists())
        with patch('core.services.user_management.send_email_with_provider'):
            enabled = self.client.post(route, data=json.dumps({'action': 'enable', 'reason': 'Appeal approved'}),
                                       content_type='application/json')
        self.assertEqual(enabled.status_code, 200)
        self.member.refresh_from_db()
        self.assertTrue(self.member.is_active)

    def test_staff_cannot_disable_users(self):
        self.client.force_login(self.staff)
        response = self.client.post(reverse('core:user_status_toggle', args=[self.member.pk]),
                                    data=json.dumps({'action': 'disable', 'reason': 'Bad request'}),
                                    content_type='application/json')
        self.assertNotEqual(response.status_code, 200)
        self.member.refresh_from_db()
        self.assertTrue(self.member.is_active)

    def test_bulk_disable_requires_reason_and_audits_each_target(self):
        self.client.force_login(self.owner)
        url = reverse('core:user_bulk_action')
        params = {'action': 'disable', 'user_ids': json.dumps([self.member.pk]), 'reason': ' '}
        invalid = self.client.post(url, params)
        self.assertEqual(invalid.status_code, 400)
        self.member.refresh_from_db()
        self.assertTrue(self.member.is_active)
        params['reason'] = 'Review completed'
        valid = self.client.post(url, params)
        self.assertEqual(valid.status_code, 200, valid.content)
        self.member.refresh_from_db()
        self.assertFalse(self.member.is_active)
        self.assertTrue(UserStatusChange.objects.filter(user=self.member, reason='Review completed').exists())
