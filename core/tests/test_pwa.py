"""PWA endpoint and privacy regression tests (no database needed)."""
import json
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase
from django.urls import reverse


class PWAFundamentalsTests(SimpleTestCase):
    def test_manifest_is_public_and_installable(self):
        response = self.client.get(reverse('pwa_manifest'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response['Content-Type'].startswith('application/manifest+json'))
        manifest = json.loads(response.content)
        self.assertEqual(manifest['scope'], '/')
        self.assertEqual(manifest['start_url'], '/app/')
        self.assertEqual(manifest['display'], 'standalone')
        for icon in manifest['icons']:
            self.assertTrue(icon['src'].startswith('/static/pwa/icons/'))
            self.assertTrue((Path(settings.BASE_DIR) / icon['src'].lstrip('/')).exists())

    def test_install_launch_redirects_to_login_without_changing_public_home(self):
        result = self.client.get(reverse('pwa_launch'))
        self.assertRedirects(result, reverse('account_login'), fetch_redirect_response=False)
        self.assertIn('no-store', result['Cache-Control'])

    def test_worker_is_root_scoped_and_not_http_cached(self):
        response = self.client.get(reverse('pwa_service_worker'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('javascript', response['Content-Type'])
        self.assertEqual(response['Service-Worker-Allowed'], '/')
        self.assertIn('no-store', response['Cache-Control'])
        self.assertIn(b"request.mode === 'navigate'", response.content)
        self.assertIn(b"request.method !== 'GET'", response.content)
        self.assertNotIn(b"caches.put(request", response.content)

    def test_no_mutation_routes_on_public_endpoints(self):
        self.assertEqual(self.client.post(reverse('pwa_manifest')).status_code, 405)
        self.assertEqual(self.client.post(reverse('pwa_service_worker')).status_code, 405)

    def test_offline_page_does_not_embed_account_data(self):
        page = (Path(settings.BASE_DIR) / 'static/pwa/offline.html').read_text()
        self.assertIn("You're offline", page)
        self.assertNotIn('csrf', page.lower())
