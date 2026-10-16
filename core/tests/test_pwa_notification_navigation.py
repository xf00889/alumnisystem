"""PWA notification click routing: auth, return paths, and open-redirect defense."""
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from django.http import HttpRequest
from django.test import SimpleTestCase, override_settings, RequestFactory
from django.urls import reverse

from core.pwa_views import notification_open


@override_settings(SECURE_SSL_REDIRECT=False)
class NotificationNavigationTests(SimpleTestCase):
    def setUp(self):
        self.setup_ready = patch(
            'setup.middleware.SetupRequiredMiddleware._is_setup_complete',
            return_value=True,
        )
        self.setup_ready.start()
        self.addCleanup(self.setup_ready.stop)

    def test_signed_out_click_prompts_login_with_exact_destination(self):
        target = '/connections/messages/?conversation=12&tab=unread'
        response = self.client.get(reverse('pwa_notification_open'), {'target': target})
        self.assertEqual(response.status_code, 302)
        location = urlsplit(response['Location'])
        self.assertEqual(location.path, reverse('account_login'))
        self.assertEqual(parse_qs(location.query)['next'], [target])
        self.assertIn('no-store', response['Cache-Control'])

    def test_logged_in_click_keeps_destination_not_dashboard(self):
        request = RequestFactory().get(reverse('pwa_notification_open'), {
            'target': '/announcements/15/?source=push',
        })
        request.user = SimpleNamespace(is_authenticated=True)
        response = notification_open(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/announcements/15/?source=push')

    def test_no_target_returns_notifications_after_login(self):
        response = self.client.get(reverse('pwa_notification_open'))
        self.assertEqual(parse_qs(urlsplit(response['Location']).query)['next'],
                         [reverse('core:all_notifications')])

    def test_external_redirects_are_rejected(self):
        bad = ('https://evil.example/', '//evil.example/', '/\\evil.example',
               'http://evil.example/', 'javascript:alert(1)',
               '/\r\nLocation: https://evil.example/', '/accounts/login/',
               '/app/notification/')
        for target in bad:
            with self.subTest(target=target):
                response = self.client.get(reverse('pwa_notification_open'), {'target': target})
                self.assertEqual(parse_qs(urlsplit(response['Location']).query)['next'],
                                 [reverse('core:all_notifications')])

    def test_post_is_not_allowed(self):
        response = self.client.post(reverse('pwa_notification_open'), {'target': '/messages/'})
        self.assertEqual(response.status_code, 405)

    def test_login_template_preserves_next_for_password_and_google(self):
        from django.conf import settings
        from pathlib import Path
        source = (Path(settings.BASE_DIR) / 'templates/account/login.html').read_text()
        self.assertIn('name="{{ redirect_field_name }}" value="{{ redirect_field_value }}"', source)
        self.assertIn('/accounts/google/login/{% if redirect_field_value %}?next=', source)
