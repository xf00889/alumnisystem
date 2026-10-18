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

    def test_first_visit_notice_is_visible_without_script_or_state_fetch(self):
        request = RequestFactory().get('/')
        response = CookieConsentBannerMiddleware(
            lambda req: HttpResponse('<html><body>Welcome</body></html>', content_type='text/html')
        )(request)
        html = response.content.decode()
        self.assertIn('id="norsuCookieConsent"', html)
        self.assertIn('This website uses cookies', html)
        self.assertNotIn('data-consent-endpoint="/api/privacy/cookie-consent/" hidden', html)
        self.assertIn('private', response['Cache-Control'])
        self.assertIn('Cookie', response['Vary'])

    def test_saved_necessary_choice_hides_notice_and_shows_settings(self):
        req = RequestFactory().get('/')
        req.COOKIES[CONSENT_COOKIE] = signing.dumps('necessary', salt=PURPOSE)
        response = CookieConsentBannerMiddleware(
            lambda request: HttpResponse('<html><body>Hello</body></html>', content_type='text/html')
        )(req)
        html = response.content.decode()
        self.assertIn('data-consent-endpoint="/api/privacy/cookie-consent/" hidden', html)
        self.assertIn('id="norsuCookieSettings"', html)
        self.assertNotIn('id="norsuCookieSettings" type="button" hidden', html)

    def test_duplicate_component_is_not_injected(self):
        request = RequestFactory().get('/')
        raw = '<html><body><div id="norsuCookieConsent"></div></body></html>'
        response = CookieConsentBannerMiddleware(
            lambda req: HttpResponse(raw, content_type='text/html')
        )(request)
        self.assertEqual(response.content.decode(), raw)
