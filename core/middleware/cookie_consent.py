"""Present optional cookie choices on normal HTML pages, including when JS is blocked.

A visitor with no stored preference must see the notice on the first response.
The website remains usable whether the preference endpoint is available or not.
"""
from django.template.loader import render_to_string
from django.utils.cache import patch_vary_headers
from core.privacy_consent import cookie_choice


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
        raw = response.content
        marker = b'</body>'
        lower = raw.lower()
        if marker not in lower or b'id="norsucookieconsent"' in lower:
            return response
        html = render_to_string('components/privacy/cookie_consent.html',
                                {'cookie_consent_choice': cookie_choice(request)},
                                request=request).encode(response.charset or 'utf-8')
        index = lower.rfind(marker)
        response.content = raw[:index] + html + b'\n' + raw[index:]
        # The visibility of the notice is a function of the user's signed choice.
        # Do not allow a shared cache to serve another visitor's consent state.
        patch_vary_headers(response, ('Cookie',))
        response['Cache-Control'] = 'private, no-store'
        if response.has_header('ETag'):
            del response['ETag']
        if response.has_header('Content-Length'):
            response['Content-Length'] = str(len(response.content))
        return response
