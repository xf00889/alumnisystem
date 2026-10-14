"""Regression tests for SMTP and email-provider safety."""
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from core.models.smtp_config import SMTPConfig
from core.models.email_provider import EmailProvider
from core.brevo_email import send_email_with_brevo


class SMTPAdminWorkflowTests(TestCase):
    def setUp(self):
        U = get_user_model()
        self.admin = U.objects.create_superuser(username='smtp-admin', email='smtp-admin@example.com', password='Test-pass-58492!')
        self.client.force_login(self.admin)

    def test_create_smtp_saves_without_activation(self):
        response = self.client.post(reverse('core:smtp_configuration_create'), {
            'name': 'Gmail', 'host': 'smtp.gmail.com', 'port': 587,
            'use_tls': 'on', 'username': 'test@gmail.com',
            'password': 'app-password-example', 'from_email': 'test@gmail.com',
            'from_name': 'NORSU Alumni', 'is_active': 'on',
        })
        self.assertEqual(response.status_code, 302)
        config = SMTPConfig.objects.get(name='Gmail')
        self.assertFalse(config.is_active)
        self.assertFalse(config.is_verified)

    def test_validation_error_keeps_form_visible(self):
        response = self.client.post(reverse('core:smtp_configuration_create'), {
            'name': 'Gmail', 'host': 'smtp.gmail.com', 'port': 'not-a-port',
            'username': 'test@gmail.com', 'password': 'x', 'from_email': 'test@gmail.com',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Unable to save configuration')
        self.assertContains(response, 'smtp.gmail.com')
        self.assertFalse(SMTPConfig.objects.exists())

    def test_edit_does_not_return_saved_password_in_html(self):
        config = SMTPConfig.objects.create(name='Existing', host='smtp.gmail.com', port=587,
            use_tls=True, username='test@gmail.com', password='not-a-displayed-secret',
            from_email='test@gmail.com', is_active=False)
        response = self.client.get(reverse('core:smtp_configuration_edit', args=[config.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'not-a-displayed-secret')

    def test_name_only_edit_preserves_verification_and_credential(self):
        config = SMTPConfig.objects.create(name='Initial', host='smtp.gmail.com', port=587,
            use_tls=True, username='test@gmail.com', password='retained-app-password',
            from_email='test@gmail.com', is_active=False, is_verified=True)
        response = self.client.post(reverse('core:smtp_configuration_edit', args=[config.pk]), {
            'name': 'Renamed', 'host': 'smtp.gmail.com', 'port': 587,
            'use_tls': 'on', 'username': 'test@gmail.com', 'password': '',
            'from_email': 'test@gmail.com', 'from_name': '',
        })
        self.assertEqual(response.status_code, 302)
        config.refresh_from_db()
        self.assertTrue(config.is_verified)
        self.assertEqual(config.password, 'retained-app-password')

    def test_unverified_smtp_cannot_be_activated(self):
        config = SMTPConfig.objects.create(name='Existing', host='smtp.gmail.com', port=587,
            use_tls=True, username='test@gmail.com', password='some-password',
            from_email='test@gmail.com', is_active=False, is_verified=False)
        response = self.client.post(reverse('core:smtp_configuration_activate', args=[config.pk]))
        self.assertEqual(response.status_code, 302)
        config.refresh_from_db()
        self.assertFalse(config.is_active)

    def test_quick_setup_success_activates_smtp_provider(self):
        with patch.object(SMTPConfig, 'test_connection', return_value=(True, 'Verified')):
            response = self.client.post(reverse('core:smtp_quick_setup'), {
                'provider': 'gmail', 'from_email':'test@gmail.com',
                'password':'example-app-password', 'from_name':'NORSU Alumni',
            }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertTrue(SMTPConfig.objects.get(host='smtp.gmail.com').is_active)
        self.assertEqual(EmailProvider.get_active_provider().provider_type, 'smtp')

    def test_quick_setup_failed_test_keeps_previous_provider(self):
        EmailProvider.objects.create(provider_type='brevo', is_active=True)
        with patch.object(SMTPConfig, 'test_connection', return_value=(False, 'Cannot connect')):
            response = self.client.post(reverse('core:smtp_quick_setup'), {
                'provider': 'gmail', 'from_email':'test@gmail.com',
                'password':'example-app-password',
            }, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['saved'])
        self.assertFalse(response.json()['success'])
        self.assertEqual(EmailProvider.get_active_provider().provider_type, 'brevo')

    def test_admin_page_denied_to_anonymous(self):
        self.client.logout()
        response = self.client.get(reverse('core:smtp_configuration_create'))
        self.assertNotEqual(response.status_code, 200)


class BrevoSenderNameTests(TestCase):
    @patch('core.brevo_email.get_brevo_settings', return_value={
        'api_key':'fake', 'api_url':'https://api.brevo.com/v3/smtp/email',
        'from_email':'verified@example.com', 'from_name':'',
    })
    @patch('core.brevo_email.requests.post')
    def test_sender_name_fallback(self, mock_post, mock_settings):
        mock_post.return_value.status_code = 201
        self.assertTrue(send_email_with_brevo('Test', 'body', ['recipient@example.com']))
        sender = mock_post.call_args.kwargs['json']['sender']
        self.assertEqual(sender['name'], 'NORSU Alumni')
