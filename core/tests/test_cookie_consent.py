"""Check CSRF, opt-in, opt-out and banner rendering, no production data."""
from django.core import signing
from django.http import HttpResponse
from django.test import TestCase, RequestFactory, override_settings
from django.urls import reverse
from core.privacy_consent import CONSENT_COOKIE, VISITOR_COOKIE, PURPOSE, analytics_consented
from core.middleware.cookie_consent import CookieConsentBannerMiddleware
from setup.models import SetupState


@override_settings(SECURE_SSL_REDIRECT=False, DEBUG=False)
class CookieConsentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        SetupState.get_setup_state().mark_complete()

    def test_default_not_opted_in(self):
        req = RequestFactory().get('/')
        self.assertFalse(analytics_consented(req))
        req.COOKIES[CONSENT_COOKIE] = 'tampered-value'
        self.assertFalse(analytics_consented(req))

    def test_get_bootstrap_returns_csrf_token(self):
        response = self.client.get(reverse('core:cookie_consent'), secure=True)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('csrfToken', data)
        self.assertTrue(data['csrfToken'])

    def test_csrf_rejects_untrusted_post(self):
        client = self.client_class(enforce_csrf_checks=True)
        response = client.post(reverse('core:cookie_consent'), {'choice': 'analytics'}, secure=True)
        self.assertEqual(response.status_code, 403)

    def test_explicit_accept_and_withdraw(self):
        endpoint = reverse('core:cookie_consent')
        response = self.client.post(endpoint, {'choice': 'analytics'}, secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(VISITOR_COOKIE, response.cookies)
        self.assertIn(CONSENT_COOKIE, response.cookies)
        self.assertTrue(response.cookies[CONSENT_COOKIE]['httponly'])
        self.assertTrue(response.cookies[CONSENT_COOKIE]['secure'])
        self.assertEqual(self.client.get(endpoint, secure=True).json()['choice'], 'analytics')
        rejected = self.client.post(endpoint, {'choice': 'necessary'}, secure=True)
        self.assertEqual(rejected.status_code, 200)
        self.assertEqual(self.client.get(endpoint, secure=True).json()['choice'], 'necessary')
        self.assertEqual(rejected.cookies[VISITOR_COOKIE].value, '')

    def test_invalid_choice_not_accepted(self):
        response = self.client.post(reverse('core:cookie_consent'), {'choice': 'ads'}, secure=True)
        self.assertEqual(response.status_code, 400)

    def test_inserts_controls_on_html_only(self):
        middleware = CookieConsentBannerMiddleware(lambda request: HttpResponse('<html><body>Hello</body></html>', content_type='text/html'))
        response = middleware(RequestFactory().get('/'))
        self.assertIn(b'norsuCookieConsent', response.content)
        self.assertIn(b'</body>', response.content)
