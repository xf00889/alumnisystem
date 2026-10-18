"""Regression coverage for anonymous cookie consent on the deployed route."""
from django.test import Client, TestCase, override_settings
from django.urls import resolve, reverse
from setup.models import SetupState
from core.privacy_consent import CONSENT_COOKIE, VISITOR_COOKIE


@override_settings(SECURE_SSL_REDIRECT=False)
class CookieEndpointRouteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        SetupState.get_setup_state().mark_complete()

    def test_registered_route_and_name(self):
        url = reverse('core:cookie_consent')
        self.assertEqual(url, '/api/privacy/cookie-consent/')
        self.assertEqual(resolve(url).view_name, 'core:cookie_consent')

    def test_anonymous_get_returns_valid_json_and_csrf(self):
        url = reverse('core:cookie_consent')
        response = self.client.get(url, secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['choice'], 'unset')
        self.assertTrue(response.json()['csrfToken'])

    def test_fresh_browser_may_save_necessary_only_with_csrf(self):
        url = reverse('core:cookie_consent')
        c = Client(enforce_csrf_checks=True)
        bootstrap = c.get(url, secure=True)
        self.assertEqual(bootstrap.status_code, 200)
        token = bootstrap.json()['csrfToken']
        response = c.post(url, {'choice': 'necessary'}, secure=True, HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['choice'], 'necessary')
        self.assertIn(CONSENT_COOKIE, response.cookies)
        self.assertNotIn(VISITOR_COOKIE, response.cookies)
        self.assertEqual(c.get(url, secure=True).json()['choice'], 'necessary')

    def test_fresh_browser_may_accept_analytics_with_csrf(self):
        url = reverse('core:cookie_consent')
        c = Client(enforce_csrf_checks=True)
        token = c.get(url, secure=True).json()['csrfToken']
        response = c.post(url, {'choice': 'analytics'}, secure=True, HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)
        self.assertIn(VISITOR_COOKIE, response.cookies)

    def test_post_without_csrf_is_rejected(self):
        url = reverse('core:cookie_consent')
        c = Client(enforce_csrf_checks=True)
        response = c.post(url, {'choice': 'analytics'}, secure=True)
        self.assertEqual(response.status_code, 403)
