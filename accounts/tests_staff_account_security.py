"""Regression tests for privileged self-service account security.

Run: python manage.py test accounts.tests_staff_profile accounts.tests_staff_account_security
"""

from unittest.mock import patch

from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import IntegrityError
from django.test import Client, TestCase
from django.urls import resolve, reverse

from alumni_directory.models import Alumni
from core.models.contact import ContactInfo

from .staff_email_change import TOKEN_MAX_AGE, create_email_change_token
from .staff_profile_views import account_email_management_gateway

User = get_user_model()


class StaffAccountSecurityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_user(username='security_staff', email='staff-security@example.com',
                                             password='PreviousStrong123!', is_staff=True)
        cls.another_staff = User.objects.create_user(username='security_other', email='other-security@example.com',
                                                     password='PreviousStrong123!', is_staff=True)
        cls.alumnus = User.objects.create_user(username='security_alumni', email='alumni-security@example.com',
                                               password='PreviousStrong123!')
        cls.dual = User.objects.create_user(username='security_dual', email='dual-security@example.com',
                                            password='PreviousStrong123!', is_staff=True)
        Alumni.objects.create(user=cls.dual, college='CAS', campus='MAIN', graduation_year=2025,
                              course='BSIT', gender='M', province='', city='', address='', is_verified=True)
        cls.coordinator = User.objects.create_user(username='security_coord', email='coord-security@example.com',
                                                   password='PreviousStrong123!')
        cls.coordinator.profile.is_alumni_coordinator = True
        cls.coordinator.profile.save(update_fields=['is_alumni_coordinator'])

    def setUp(self):
        setup_guard = patch('setup.middleware.SetupRequiredMiddleware._is_setup_complete', return_value=True)
        setup_guard.start()
        self.addCleanup(setup_guard.stop)
        cache.clear()
        self.client.force_login(self.staff)

    def _password_data(self, current='PreviousStrong123!', new='NewStrongPassword987!'):
        return {'old_password': current, 'new_password1': new, 'new_password2': new}

    def _email_data(self, email='changed-security@example.com', current='PreviousStrong123!'):
        return {'new_email': email, 'current_password': current}

    def _token_url(self, user=None, email='changed-security@example.com'):
        return reverse('accounts:confirm_staff_email', kwargs={
            'token': create_email_change_token(user or self.staff, email)})

    def test_staff_profile_has_email_and_password_links(self):
        resp = self.client.get(reverse('accounts:staff_profile'))
        self.assertContains(resp, 'Change Email')
        self.assertContains(resp, 'Change Password')

    def test_staff_only_routes_block_normal_alumni(self):
        self.client.force_login(self.alumnus)
        for route in ('accounts:staff_profile', 'accounts:change_staff_email', 'accounts:change_staff_password'):
            self.assertEqual(self.client.get(reverse(route)).status_code, 403)

    def test_coordinator_and_dual_role_staff_can_access_credential_forms(self):
        for user in (self.coordinator, self.dual):
            self.client.force_login(user)
            self.assertEqual(self.client.get(reverse('accounts:change_staff_email')).status_code, 200)
            self.assertEqual(self.client.get(reverse('accounts:change_staff_password')).status_code, 200)

    def test_password_rejects_missing_or_incorrect_old_password(self):
        url = reverse('accounts:change_staff_password')
        for incorrect in ('', 'wrong'):
            response = self.client.post(url, self._password_data(incorrect))
            self.assertEqual(response.status_code, 200)
            self.staff.refresh_from_db()
            self.assertTrue(self.staff.check_password('PreviousStrong123!'))

    def test_password_change_keeps_this_session_and_rotates_password(self):
        response = self.client.post(reverse('accounts:change_staff_password'), self._password_data())
        self.assertRedirects(response, reverse('accounts:staff_profile'))
        self.staff.refresh_from_db()
        self.assertTrue(self.staff.check_password('NewStrongPassword987!'))
        self.assertEqual(self.client.get(reverse('accounts:staff_profile')).status_code, 200)

    def test_legacy_endpoint_cannot_bypass_old_password(self):
        url = reverse('accounts:change_password')
        self.assertEqual(self.client.post(url, {'new_password1': 'NewStrongPassword987!',
                                                'new_password2': 'NewStrongPassword987!'}).status_code, 200)
        self.staff.refresh_from_db()
        self.assertTrue(self.staff.check_password('PreviousStrong123!'))

    def test_legacy_endpoint_accepts_valid_old_password(self):
        self.assertRedirects(self.client.post(reverse('accounts:change_password'), self._password_data()),
                             reverse('accounts:staff_profile'))
        self.staff.refresh_from_db()
        self.assertTrue(self.staff.check_password('NewStrongPassword987!'))

    def test_email_rejects_incorrect_current_password(self):
        with patch('accounts.staff_profile_views.send_email_change_link') as mock_send:
            response = self.client.post(reverse('accounts:change_staff_email'), self._email_data(current='wrong'))
        self.assertEqual(response.status_code, 200)
        mock_send.assert_not_called()
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.email, 'staff-security@example.com')

    def test_email_rejects_case_insensitive_duplicate_user_email(self):
        response = self.client.post(reverse('accounts:change_staff_email'),
                                    self._email_data(email='ALUMNI-SECURITY@example.com'))
        self.assertContains(response, 'already in use')

    def test_email_rejects_duplicate_allauth_identity(self):
        EmailAddress.objects.create(user=self.alumnus, email='other-login@example.com', verified=True)
        response = self.client.post(reverse('accounts:change_staff_email'),
                                    self._email_data(email='OTHER-LOGIN@example.com'))
        self.assertContains(response, 'already in use')

    def test_request_link_does_not_change_email_before_confirmation(self):
        with patch('accounts.staff_email_change.send_email_with_provider', return_value=1) as send:
            self.assertRedirects(self.client.post(reverse('accounts:change_staff_email'), self._email_data()),
                                 reverse('accounts:staff_profile'))
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.email, 'staff-security@example.com')
        self.assertEqual(send.call_args.kwargs['recipient_list'], ['changed-security@example.com'])
        self.assertIn('/accounts/staff-profile/confirm-email/', send.call_args.kwargs['message'])

    def test_email_send_failure_leaves_old_address_intact(self):
        with patch('accounts.staff_email_change.send_email_with_provider', side_effect=RuntimeError('smtp failed')):
            response = self.client.post(reverse('accounts:change_staff_email'), self._email_data())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'could not be sent')
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.email, 'staff-security@example.com')

    def test_confirmation_post_rejects_missing_csrf_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.staff)
        response = csrf_client.post(self._token_url())
        self.assertEqual(response.status_code, 403)
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.email, 'staff-security@example.com')

    def test_confirmation_get_is_read_only_and_post_updates_all_three_stores(self):
        EmailAddress.objects.create(user=self.staff, email=self.staff.email, primary=True, verified=True)
        ContactInfo.objects.create(user=self.staff, contact_type='EMAIL', contact_value=self.staff.email,
                                   is_primary=True, is_verified=True)
        url = self._token_url()
        self.assertEqual(self.client.get(url).status_code, 200)
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.email, 'staff-security@example.com')
        with patch('accounts.staff_email_change.send_email_with_provider', return_value=1) as mock_send:
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(url)
        self.assertRedirects(response, reverse('accounts:staff_profile'))
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.email, 'changed-security@example.com')
        self.assertTrue(EmailAddress.objects.filter(user=self.staff, email=self.staff.email,
                                                    primary=True, verified=True).exists())
        self.assertFalse(EmailAddress.objects.filter(user=self.staff, email='staff-security@example.com').exists())
        self.assertTrue(ContactInfo.objects.filter(user=self.staff, contact_type='EMAIL',
                                                   contact_value=self.staff.email, is_primary=True,
                                                   is_verified=True).exists())
        self.assertFalse(ContactInfo.objects.filter(user=self.staff, contact_type='EMAIL',
                                                    contact_value='staff-security@example.com').exists())
        mock_send.assert_called_once()
        self.assertEqual(mock_send.call_args.kwargs['recipient_list'], ['staff-security@example.com'])

    def test_replay_token_is_rejected(self):
        url = self._token_url()
        self.assertRedirects(self.client.post(url), reverse('accounts:staff_profile'))
        self.assertEqual(self.client.post(url).status_code, 400)

    def test_cross_account_token_is_rejected(self):
        url = self._token_url()
        self.client.force_login(self.another_staff)
        self.assertEqual(self.client.get(url).status_code, 400)
        self.assertEqual(self.client.post(url).status_code, 400)

    def test_tampered_token_is_rejected(self):
        token = create_email_change_token(self.staff, 'tampered@example.com')
        url = reverse('accounts:confirm_staff_email', kwargs={'token': token + 'bad'})
        self.assertEqual(self.client.post(url).status_code, 400)

    def test_expired_token_is_rejected(self):
        import time
        now = time.time()
        with patch('django.core.signing.time.time', return_value=now):
            token = create_email_change_token(self.staff, 'new-expired@example.com')
        with patch('django.core.signing.time.time', return_value=now + TOKEN_MAX_AGE + 1):
            self.assertEqual(self.client.post(reverse('accounts:confirm_staff_email',
                                                     kwargs={'token': token})).status_code, 400)

    def test_password_rotation_invalidates_pending_email_link(self):
        url = self._token_url()
        self.client.post(reverse('accounts:change_staff_password'), self._password_data())
        self.assertEqual(self.client.post(url).status_code, 400)

    def test_email_claimed_by_other_user_before_confirmation_rejected(self):
        url = self._token_url()
        self.another_staff.email = 'changed-security@example.com'
        self.another_staff.save(update_fields=['email'])
        self.assertEqual(self.client.post(url).status_code, 400)
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.email, 'staff-security@example.com')

    def test_transaction_rolls_back_when_contact_info_fails(self):
        EmailAddress.objects.create(user=self.staff, email=self.staff.email, primary=True, verified=True)
        with patch.object(ContactInfo, 'save', side_effect=IntegrityError('simulated write failure')):
            response = self.client.post(self._token_url())
        self.assertEqual(response.status_code, 500)
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.email, 'staff-security@example.com')
        self.assertTrue(EmailAddress.objects.filter(user=self.staff, email=self.staff.email,
                                                    primary=True).exists())

    def test_email_change_preserves_other_unrelated_secondary_contacts(self):
        EmailAddress.objects.create(user=self.staff, email=self.staff.email, primary=True, verified=True)
        EmailAddress.objects.create(user=self.staff, email='secondary-security@example.com',
                                    primary=False, verified=True)
        ContactInfo.objects.create(user=self.staff, contact_type='EMAIL', contact_value=self.staff.email,
                                   is_primary=True, is_verified=True)
        ContactInfo.objects.create(user=self.staff, contact_type='EMAIL',
                                   contact_value='secondary-security@example.com', is_primary=False)
        self.client.post(self._token_url())
        self.assertTrue(EmailAddress.objects.filter(user=self.staff,
                                                    email='secondary-security@example.com', primary=False).exists())
        self.assertTrue(ContactInfo.objects.filter(user=self.staff, contact_type='EMAIL',
                                                   contact_value='secondary-security@example.com',
                                                   is_primary=False).exists())

    def test_email_attempts_are_rate_limited(self):
        url = reverse('accounts:change_staff_email')
        for _ in range(5):
            self.assertEqual(self.client.post(url, self._email_data(current='wrong')).status_code, 200)
        self.assertEqual(self.client.post(url, self._email_data(current='wrong')).status_code, 403)

    def test_email_change_requires_usable_local_password(self):
        self.staff.set_unusable_password()
        self.staff.save(update_fields=['password'])
        self.client.force_login(self.staff)
        response = self.client.post(reverse('accounts:change_staff_email'), self._email_data())
        self.assertContains(response, 'no local password')

    def test_allauth_staff_email_endpoint_is_guarded(self):
        gateway = resolve('/accounts/email/').func
        self.assertEqual(gateway, account_email_management_gateway)
        self.assertRedirects(self.client.get('/accounts/email/'), reverse('accounts:change_staff_email'))
        self.assertEqual(self.client.post('/accounts/email/', {'email': 'fake@example.com', 'action_add': '1'}).status_code, 403)
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.email, 'staff-security@example.com')

    def test_nonstaff_allauth_email_route_still_renders(self):
        self.client.force_login(self.alumnus)
        self.assertEqual(self.client.get('/accounts/email/').status_code, 200)

    def test_no_implicit_alumni_identity_for_staff(self):
        self.assertFalse(Alumni.objects.filter(user=self.staff).exists())
        self.client.get(reverse('accounts:staff_profile'))
        self.assertFalse(Alumni.objects.filter(user=self.staff).exists())
