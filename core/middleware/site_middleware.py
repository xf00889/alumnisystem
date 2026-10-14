"""Site domain is configured administratively, never from untrusted request Host headers.

The previous middleware updated django_site on *every request*. This created
race conditions between www, bare domain and IP requests, and could affect
OAuth redirects and password reset links. The middleware remains for import
compatibility but performs no database writes.
"""
class EnsureSiteMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)
