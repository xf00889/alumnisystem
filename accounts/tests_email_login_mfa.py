"""Additional login-stage checks. Must be run on the isolated Django test DB."""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from allauth.account.models import EmailAddress
from allauth.mfa import totp

from accounts.email_login_mfa import KEY, MAX_ATTEMPTS, email_enabled, verified_email
from core.testing_clients import CompletedPortalSetupMixin
from accounts.models import EmailLoginMFASettings


@override_settings(SECURE_SSL_REDIRECT=False, EMAIL_LOGIN_MFA_ROLLOUT=True)
class EmailLoginMFATests(CompletedPortalSetupMixin, TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='emailstage', email='emailstage@example.org', password='StrongLoginPassword!810'
        )
        EmailAddress.objects.create(user=self.user, email=self.user.email, verified=True, primary=True)

    def test_disabled_by_default(self):
        self.assertFalse(email_enabled(self.user))
        self.assertTrue(verified_email(self.user))
        self.assertEqual(self.client.get(reverse('accounts:login_email_challenge'), secure=True).status_code, 302)

    @patch('accounts.email_login_mfa.send_email_with_provider', return_value=True)
    def test_email_opt_in_blocks_session_login_until_code(self, send):
        EmailLoginMFASettings.objects.create(user=self.user, enabled=True)
        r = self.client.post(reverse('account_login'), {
            'login': self.user.email, 'password': 'StrongLoginPassword!810',
        }, secure=True)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r['Location'], reverse('accounts:login_email_challenge'))
        self.assertNotIn('_auth_user_id', self.client.session)
        get = self.client.get(reverse('accounts:login_email_challenge'), secure=True)
        self.assertEqual(get.status_code, 200)
        send.assert_called_once()
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertNotIn('code', self.client.session.get(KEY, {}))
        incorrect = self.client.post(reverse('accounts:login_email_challenge'), {
            'code': '000000', 'action': 'verify',
        }, secure=True)
        self.assertEqual(incorrect.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    @patch('accounts.email_login_mfa.send_email_with_provider', return_value=True)
    def test_resend_cooldown(self, send):
        EmailLoginMFASettings.objects.create(user=self.user, enabled=True)
        self.client.post(reverse('account_login'), {
            'login': self.user.email, 'password': 'StrongLoginPassword!810',
        }, secure=True)
        self.client.get(reverse('accounts:login_email_challenge'), secure=True)
        self.client.post(reverse('accounts:login_email_challenge'), {
            'action': 'resend',
        }, secure=True)
        self.assertEqual(send.call_count, 1)

    @patch('accounts.email_login_mfa.send_email_with_provider', return_value=True)
    def test_totp_still_first_when_both_enabled(self, send):
        EmailLoginMFASettings.objects.create(user=self.user, enabled=True)
        totp.TOTP.activate(self.user, totp.generate_totp_secret())
        response = self.client.post(reverse('account_login'), {
            'login': self.user.email, 'password': 'StrongLoginPassword!810',
        }, secure=True)
        self.assertEqual(response['Location'], reverse('mfa_authenticate'))
        view = self.client.get(reverse('mfa_authenticate'), secure=True)
        self.assertContains(view, 'Try another way')
        self.assertEqual(send.call_count, 0)

    def test_unverified_email_not_allowed_as_method(self):
        EmailAddress.objects.filter(user=self.user).update(verified=False)
        EmailLoginMFASettings.objects.create(user=self.user, enabled=True)
        self.assertFalse(verified_email(self.user))
