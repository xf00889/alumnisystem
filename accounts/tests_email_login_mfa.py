"""Additional login-stage checks. Must be run on the isolated Django test DB."""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from allauth.mfa import totp

from accounts.email_login_mfa import KEY, MAX_ATTEMPTS, email_enabled, verified_email, _google_identity_confirms_address
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
    def test_email_challenge_form_is_accessible_and_submits_only_on_action(self, send):
        EmailLoginMFASettings.objects.create(user=self.user, enabled=True)
        self.client.post(reverse('account_login'), {
            'login': self.user.email, 'password': 'StrongLoginPassword!810',
        }, secure=True)
        response = self.client.get(reverse('accounts:login_email_challenge'), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'mfa-card--email')
        self.assertContains(response, 'Sign-in security · Step 2 of 2')
        self.assertContains(response, 'autocomplete="one-time-code"')
        self.assertContains(response, 'inputmode="numeric"')
        self.assertContains(response, 'aria-describedby="email-code-help"')
        self.assertContains(response, 'name="action" value="verify"')
        self.assertContains(response, 'name="action" value="resend"')
        self.assertContains(response, 'Back to sign in')
        self.assertNotContains(response, 'oninput=')
        self.assertNotContains(response, 'onkeyup=')
        self.assertNotContains(response, 'autofocus="submit"')
        self.assertNotIn('_auth_user_id', self.client.session)
        send.assert_called_once()

    @patch('accounts.email_login_mfa.send_email_with_provider', return_value=True)
    def test_email_only_challenge_omits_authenticator_link(self, send):
        EmailLoginMFASettings.objects.create(user=self.user, enabled=True)
        self.client.post(reverse('account_login'), {
            'login': self.user.email, 'password': 'StrongLoginPassword!810',
        }, secure=True)
        response = self.client.get(reverse('accounts:login_email_challenge'), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Use authenticator app instead')

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

    def test_google_identity_confirmation_requires_matching_verified_claim(self):
        email = self.user.email
        matches = (
            {'email': ' EMAILSTAGE@example.org ', 'email_verified': True},
            {'email': email, 'email_verified': 'true'},
            {'email': email, 'verified_email': True},
        )
        for payload in matches:
            with self.subTest(accepted=payload):
                self.assertTrue(_google_identity_confirms_address(payload, email))
        rejected = (
            None,
            {},
            {'email': email},
            {'email': email, 'email_verified': False},
            {'email': email, 'email_verified': 'yes'},
            {'email': 'unrelated@example.org', 'email_verified': True},
            {'email': email, 'email_verified': 1},
        )
        for payload in rejected:
            with self.subTest(rejected=payload):
                self.assertFalse(_google_identity_confirms_address(payload, email))

    def test_verified_google_sso_address_can_enable_email_verification(self):
        # Some OAuth accounts have a linked Google identity but no EmailAddress row.
        EmailAddress.objects.filter(user=self.user).delete()
        SocialAccount.objects.create(
            user=self.user, provider='google', uid='google-verified-test',
            extra_data={'email': 'EmailStage@example.org', 'email_verified': True},
        )
        self.assertTrue(verified_email(self.user))
        self.client.force_login(self.user)
        response = self.client.get(reverse('accounts:security_dashboard'), secure=True)
        self.assertContains(response, 'Enable email verification')
        self.assertNotContains(response, 'Verify your registered email before enabling')

    def test_linked_google_cannot_verify_unrelated_or_unconfirmed_email(self):
        EmailAddress.objects.filter(user=self.user).delete()
        google = SocialAccount.objects.create(
            user=self.user, provider='google', uid='google-unverified-test',
            extra_data={'email': 'someoneelse@example.org', 'email_verified': True},
        )
        self.assertFalse(verified_email(self.user))
        google.extra_data = {'email': self.user.email, 'email_verified': False}
        google.save(update_fields=['extra_data'])
        self.assertFalse(verified_email(self.user))
        google.extra_data = {'email': self.user.email, 'email_verified': True}
        google.save(update_fields=['extra_data'])
        google.refresh_from_db()
        self.assertTrue(_google_identity_confirms_address(google.extra_data, self.user.email))
        self.assertTrue(verified_email(self.user))
        self.user.email = 'changed@example.org'
        self.user.save(update_fields=['email'])
        self.assertFalse(verified_email(self.user))

    @override_settings(EMAIL_LOGIN_MFA_ROLLOUT=False)
    def test_rollout_disabled_has_distinct_message_from_unverified_email(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('accounts:security_dashboard'), secure=True)
        self.assertContains(response, 'not currently available')
        self.assertNotContains(response, 'Verify your registered email before enabling')

    def test_unverified_email_not_allowed_as_method(self):
        EmailAddress.objects.filter(user=self.user).update(verified=False)
        EmailLoginMFASettings.objects.create(user=self.user, enabled=True)
        self.assertFalse(verified_email(self.user))
