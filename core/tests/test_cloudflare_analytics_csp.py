"""Keep Cloudflare Web Analytics compatible with NORSU's existing CSP.

These tests don't make network requests or change Cloudflare protection settings.
"""

from django.conf import settings
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase
from csp.middleware import CSPMiddleware


class CloudflareWebAnalyticsCSPTests(SimpleTestCase):
    def test_allowlist_is_script_only_and_keeps_reporting_same_origin(self):
        # The automatic Cloudflare beacon can use a versioned /beacon.min.js/...
        # URL, so a path-exact CSP entry might not cover all deployed scripts.
        self.assertIn(
            "https://static.cloudflareinsights.com", settings.CSP_SCRIPT_SRC
        )
        self.assertIn("'self'", settings.CSP_CONNECT_SRC)
        self.assertNotIn(
            "https://static.cloudflareinsights.com", settings.CSP_DEFAULT_SRC
        )
        self.assertNotIn("*", settings.CSP_SCRIPT_SRC)
        self.assertNotIn("*", settings.CSP_CONNECT_SRC)

    def test_effective_django_csp_header_allows_beacon(self):
        # Validate the HTTP header rather than only checking the settings tuple.
        request = RequestFactory().get("/")
        response = CSPMiddleware(lambda req: HttpResponse("ok"))(request)
        policy = response.get("Content-Security-Policy", "")
        self.assertIn("script-src ", policy)
        self.assertIn("https://static.cloudflareinsights.com", policy)
        self.assertIn("connect-src ", policy)
        self.assertIn("'self'", policy)
