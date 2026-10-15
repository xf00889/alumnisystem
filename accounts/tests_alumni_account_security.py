"""Django tests for alumni account-security UX and credential recovery.

Run in an isolated test DB with configured allauth and site settings:
  python manage.py test accounts.tests_alumni_account_security -v 2
"""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator

from core.testing_clients import CompletedPortalSetupMixin, HTTPSClient

from allauth.account.models import EmailAddress


class AlumniAccountSecurityTests(CompletedPortalSetupMixin, TestCase):
    client_class = HTTPSClient

    def setUp(self):
        cache.clear()
        User = get_user_model()
        self.user = User.objects.create_user(
            username='password-alumni@example.net',
            email='password-alumni@example.net',
            password='AnExistingPassword!123',
            is_active=True,
        )
        EmailAddress.objects.create(
            user=self.user,
            email=self.user.email,
            primary=True,
            verified=True,
        )

    def test_security_dashboard_rejects_anonymous_user(self):
        r = self.client.get(reverse('accounts:security_dashboard'))
        self.assertIn(r.status_code, (301, 302))

    def test_security_dashboard_shows_password_actions_and_mfa(self):
        self.client.force_login(self.user)
        r = self.client.get(reverse('accounts:security_dashboard'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Change password')
        self.assertContains(r, 'Forgot current password?')
        self.assertContains(r, 'Two-factor authentication')

    def test_mfa_management_requires_login(self):
        response = self.client.get(reverse('mfa_index'))
        self.assertIn(response.status_code, (301, 302))

    def test_mfa_management_uses_alumni_nav_after_authentication(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('mfa_index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Security Dashboard')
        self.assertContains(response, 'Alumni Network')

    def test_change_password_requires_existing_password(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('accounts:change_password'), {
            'old_password': 'wrong-old-password',
            'new_password1': 'UpdatedExample!124',
            'new_password2': 'UpdatedExample!124',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.user.check_password('AnExistingPassword!123'))
        self.assertContains(response, 'current password', status_code=200)

    @patch('accounts.alumni_password_views.send_email_with_provider', return_value=True)
    def test_password_link_request_signed_in_targets_own_email(self, send):
        self.client.force_login(self.user)
        response = self.client.post(reverse('accounts:password_recovery_request'), {
            'email': 'not-the-account@example.org',
        })
        self.assertRedirects(response, reverse('accounts:password_recovery_requested'), fetch_redirect_response=False)
        self.assertEqual(self.client.get(reverse('accounts:password_recovery_requested'), secure=True).status_code, 200)
        self.assertEqual(send.call_count, 1)
        self.assertEqual(send.call_args.kwargs['recipient_list'], [self.user.email])

    @patch('accounts.alumni_password_views.send_email_with_provider', return_value=True)
    def test_anonymous_user_cannot_request_authenticated_password_link(self, send):
        url = reverse('accounts:password_recovery_request')
        response = self.client.post(url, {'email': self.user.email})
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])
        send.assert_not_called()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])

    def test_signed_in_recovery_form_uses_alumni_navigation_and_locked_email(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('accounts:password_recovery_request'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'readonly')
        self.assertContains(response, self.user.email)
        self.assertContains(response, 'Alumni Network')

    def test_sent_page_requires_login(self):
        response = self.client.get(reverse('accounts:password_recovery_requested'))
        self.assertEqual(response.status_code, 302)
        self.client.force_login(self.user)
        response = self.client.get(reverse('accounts:password_recovery_requested'))
        self.assertEqual(response.status_code, 200)

    def test_signed_link_can_change_password_but_does_not_sign_in(self):
        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        url = reverse('accounts:password_recovery_confirm', kwargs={
            'uidb64': uidb64, 'token': token,
        })
        anon = HTTPSClient()
        response = anon.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('set-password', response['Location'])
        response = anon.get(response['Location'])
        self.assertEqual(response.status_code, 200)
        response = anon.post(response.wsgi_request.path, {
            'new_password1': 'NewCredential!456',
            'new_password2': 'NewCredential!456',
        })
        self.assertRedirects(response, reverse('accounts:password_recovery_complete'), fetch_redirect_response=False)
        self.assertEqual(anon.get(reverse('accounts:password_recovery_complete'), secure=True).status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewCredential!456'))
        self.assertNotIn('_auth_user_id', anon.session)
        # Old token must become invalid after password changes.
        self.assertEqual(anon.get(url).status_code, 200)
        self.assertContains(anon.get(url), 'invalid', status_code=200)

    @patch('accounts.alumni_password_views.send_email_with_provider', return_value=True)
    def test_google_only_user_can_request_password_setup(self, send):
        self.user.set_unusable_password()
        self.user.save(update_fields=['password'])
        self.client.force_login(self.user)
        r = self.client.get(reverse('accounts:security_dashboard'))
        self.assertContains(r, 'Set a password via email verification')
        r = self.client.get(reverse('accounts:change_password'))
        self.assertRedirects(r, reverse('accounts:password_recovery_request'), fetch_redirect_response=False)
        self.assertEqual(self.client.get(reverse('accounts:password_recovery_request'), secure=True).status_code, 200)
        r = self.client.post(reverse('accounts:password_recovery_request'), {'email': self.user.email})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(send.call_count, 1)
