"""Integration tests; run with `python manage.py test accounts.tests_two_factor_security`."""
from core.testing_clients import HTTPSClient

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from allauth.account.models import EmailAddress
from allauth.mfa import totp
from allauth.mfa.models import Authenticator


class AlumniTwoFactorLoginTests(TestCase):
    client_class = HTTPSClient
    def setUp(self):
        self.email = 'mfaalumni@example.org'
        self.password = 'AnExamplePassword!9305'
        self.user = get_user_model().objects.create_user(
            username=self.email, email=self.email,
            password=self.password, is_active=True,
        )
        EmailAddress.objects.create(
            user=self.user, email=self.email, primary=True, verified=True,
        )

    def test_security_dashboard_displays_disabled_then_enabled_state(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('accounts:security_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Set up two-factor authentication')

        totp.TOTP.activate(self.user, totp.generate_totp_secret())
        response = self.client.get(reverse('accounts:security_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Manage 2FA and recovery codes')

    def test_password_login_stops_at_mfa_stage(self):
        totp.TOTP.activate(self.user, totp.generate_totp_secret())
        response = self.client.post(
            reverse('account_login'),
            {'login': self.email, 'password': self.password},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('mfa_authenticate'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_challenge_requires_correct_code_before_session_authentication(self):
        secret = totp.generate_totp_secret()
        totp.TOTP.activate(self.user, secret)
        self.client.post(reverse('account_login'), {'login': self.email, 'password': self.password})
        incorrect = self.client.post(reverse('mfa_authenticate'), {'code': 'not-a-real-code'})
        self.assertEqual(incorrect.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

        code = totp.format_hotp_value(totp.hotp_value(secret, totp.hotp_counter_from_time()))
        result = self.client.post(reverse('mfa_authenticate'), {'code': code})
        self.assertEqual(result.status_code, 302)
        self.assertEqual(str(self.client.session.get('_auth_user_id')), str(self.user.pk))

    def test_single_active_authenticator_record(self):
        secret = totp.generate_totp_secret()
        totp.TOTP.activate(self.user, secret)
        authenticator = Authenticator.objects.get(user=self.user, type=Authenticator.Type.TOTP)
        self.assertTrue(authenticator.data['secret'].startswith('v1:'))
        self.assertNotEqual(authenticator.data['secret'], secret)
