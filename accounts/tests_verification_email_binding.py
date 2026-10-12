"""Signup verification must use a session-bound recipient, not user-supplied email.

Run: python manage.py test accounts.tests_verification_email_binding
"""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .security import SecurityCodeManager


class VerificationEmailBindingTests(TestCase):
    def setUp(self):
        setup_check = patch('setup.middleware.SetupRequiredMiddleware._is_setup_complete', return_value=True)
        setup_check.start()
        self.addCleanup(setup_check.stop)
        User = get_user_model()
        self.owner = User.objects.create_user(
            username='verifier', email='verifier@example.com', password='Test-password-102!', is_active=False,
        )
        self.other = User.objects.create_user(
            username='other-verifier', email='other@example.com', password='Test-password-102!', is_active=False,
        )
        self.url = reverse('accounts:verify_email')
        self.resend = reverse('accounts:resend_verification_code')

    def bind(self):
        session = self.client.session
        session['pending_verification_user_id'] = self.owner.pk
        session.save()

    def test_email_is_readonly_and_not_selected_from_query_string(self):
        self.bind()
        response = self.client.get(self.url + '?email=other@example.com')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user_email'], self.owner.email)
        self.assertContains(response, 'readonly')
        self.assertNotContains(response, 'value="other@example.com"')

    def test_forged_email_cannot_activate_another_account(self):
        self.bind()
        SecurityCodeManager.store_code(self.other.email, '123456', 'signup')
        response = self.client.post(self.url, {'email': self.other.email, 'verification_code': '123456'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('email', response.context['form'].errors)
        self.owner.refresh_from_db()
        self.other.refresh_from_db()
        self.assertFalse(self.owner.is_active)
        self.assertFalse(self.other.is_active)

    def test_valid_session_bound_account_verifies_and_clears_binding(self):
        self.bind()
        SecurityCodeManager.store_code(self.owner.email, '654321', 'signup')
        response = self.client.post(self.url, {'email': self.owner.email, 'verification_code': '654321'})
        self.assertEqual(response.status_code, 302)
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.is_active)
        self.other.refresh_from_db()
        self.assertFalse(self.other.is_active)
        self.assertNotIn('pending_verification_user_id', self.client.session)

    def test_direct_email_url_without_session_cannot_start_verification(self):
        response = self.client.get(self.url + '?email=' + self.owner.email)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        response = self.client.post(self.url, {'email': self.owner.email, 'verification_code': '123456'})
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

    def test_resend_without_session_cannot_choose_target(self):
        response = self.client.post(self.resend, {'email': self.other.email})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(response.json()['success'])

    @patch('accounts.security_views.is_runtime_debug_enabled', return_value=False)
    @patch('accounts.security_views.RateLimiter.record_attempt')
    @patch('accounts.security_views.RateLimiter.is_rate_limited', return_value=False)
    @patch('core.email_utils.send_email_with_provider', return_value=True)
    def test_resend_ignores_forged_target(self, sender, limited, record, debug):
        self.bind()
        response = self.client.post(self.resend, {'email': self.other.email})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(sender.call_args.kwargs['recipient_list'], [self.owner.email])

    def test_inactive_account_session_resolves_to_same_verified_account(self):
        session = self.client.session
        session['inactive_account_email'] = self.owner.email
        session.save()
        response = self.client.get(self.url + '?email=' + self.other.email)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user_email'], self.owner.email)
        self.assertEqual(self.client.session['pending_verification_user_id'], self.owner.pk)

    def test_countdown_ignores_untrusted_email(self):
        self.bind()
        url = reverse('accounts:check_resend_countdown')
        with patch('accounts.security_views.RateLimiter.is_rate_limited', return_value=False) as check:
            response = self.client.post(url, {'email': self.other.email})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['can_resend'])
        self.assertEqual(check.call_args.args[0], self.owner.email)

    def test_inactive_resend_ignores_forged_target(self):
        self.bind()
        url = reverse('accounts:resend_verification_from_inactive')
        with patch('accounts.security_views.RateLimiter.is_rate_limited', return_value=False), \
             patch('accounts.security_views.RateLimiter.record_attempt'), \
             patch('accounts.security_views.is_runtime_debug_enabled', return_value=False), \
             patch('core.email_utils.send_email_with_provider', return_value=True) as sender:
            response = self.client.post(url, {'email': self.other.email})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(sender.call_args.kwargs['recipient_list'], [self.owner.email])

    def test_inactive_resend_without_session_cannot_send(self):
        url = reverse('accounts:resend_verification_from_inactive')
        with patch('core.email_utils.send_email_with_provider') as sender:
            response = self.client.post(url, {'email': self.other.email})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['success'])
        sender.assert_not_called()
