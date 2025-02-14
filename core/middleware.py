from django.http import HttpResponseRedirect
from django.conf import settings

class ForceHTTPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # If trying to access via HTTPS, redirect to HTTP
        if request.headers.get('X-Forwarded-Proto', '').lower() == 'https' or request.headers.get('X-Forwarded-Protocol', '').lower() == 'https':
            url = request.build_absolute_uri()
            if url.startswith('https://'):
                url = 'http://' + url[8:]
                return HttpResponseRedirect(url)
        
        response = self.get_response(request)
        
        # Remove HTTPS-related security headers
        if 'Strict-Transport-Security' in response.headers:
            del response.headers['Strict-Transport-Security']
        
        # Ensure headers are set to development-friendly values
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Convert any HTTPS URLs in Location header to HTTP
        if 'Location' in response.headers and response.headers['Location'].startswith('https://'):
            response.headers['Location'] = 'http://' + response.headers['Location'][8:]
        
        return response 