"""Attach consent controls without replacing the site's many changing base templates."""
from django.template.loader import render_to_string


class CookieConsentBannerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if (request.method != 'GET' or response.status_code != 200
                or getattr(response, 'streaming', False)
                or response.get('Content-Encoding')
                or 'text/html' not in response.get('Content-Type', '').lower()
                or request.headers.get('HX-Request') == 'true'):
            return response
        # ETags / content lengths must not refer to pre-injection HTML.
        raw = response.content
        marker = b'</body>'
        if marker not in raw.lower():
            return response
        html = render_to_string('components/privacy/cookie_consent.html', request=request).encode(response.charset or 'utf-8')
        ix = raw.lower().rfind(marker)
        response.content = raw[:ix] + html + b'\n' + raw[ix:]
        if response.has_header('ETag'):
            del response['ETag']
        if response.has_header('Content-Length'):
            response['Content-Length'] = str(len(response.content))
        return response
