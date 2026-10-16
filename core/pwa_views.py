"""Public, credential-free PWA endpoints. No database access or personal content."""
from pathlib import Path
from urllib.parse import urlsplit

from django.conf import settings
from django.shortcuts import redirect
from django.contrib.auth.views import redirect_to_login
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.cache import never_cache


@never_cache
@require_GET
def app_launch(request):
    """The PWA launch URL, deliberately separate from the public home page.

    Anonymous installations open the existing login page; authenticated users
    follow the existing role and registration-aware home routing.
    """
    if request.user.is_authenticated:
        return redirect('core:home')
    return redirect('account_login')


def _safe_notification_destination(value):
    """Accept only local path-and-query destinations, never external redirects.

    A push notification is untrusted input to the browser and can be clicked
    after the authentication session expires. Preserve navigation intent while
    letting the destination itself enforce role and object permissions.
    """
    fallback = reverse('core:all_notifications')
    if not isinstance(value, str) or not value or len(value) > 1024:
        return fallback
    if not value.startswith('/') or value.startswith('//') or '\\' in value:
        return fallback
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        return fallback
    try:
        parsed = urlsplit(value)
    except ValueError:
        return fallback
    if parsed.scheme or parsed.netloc or not parsed.path.startswith('/'):
        return fallback
    if parsed.path in (reverse('account_login'), reverse('pwa_notification_open')):
        return fallback
    return value


@never_cache
@require_GET
def notification_open(request):
    """A click-through entry point for installed-app push notifications.

    Anonymous visitors sign in and return to the original destination. Already
    authenticated visitors go directly to that destination. This gateway never
    fetches protected content and never bypasses destination authorization.
    """
    target = _safe_notification_destination(request.GET.get('target'))
    if not request.user.is_authenticated:
        return redirect_to_login(target, login_url=reverse('account_login'))
    return redirect(target)


@require_GET
def manifest(request):
    """Serve the manifest at the origin root with the proper MIME type."""
    icons = [
        {"src": "/static/pwa/icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
        {"src": "/static/pwa/icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
        {"src": "/static/pwa/icons/icon-maskable-192.png", "sizes": "192x192", "type": "image/png", "purpose": "maskable"},
        {"src": "/static/pwa/icons/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
    ]
    response = JsonResponse({
        "id": "/",
        "name": "NORSU Alumni Network",
        "short_name": "NORSU Alumni",
        "description": "Connect with the Negros Oriental State University alumni community.",
        "lang": "en",
        "start_url": "/app/",
        "scope": "/",
        "display": "standalone",
        "background_color": "#f7f5f0",
        "theme_color": "#182744",
        "icons": icons,
        "shortcuts": [
            {"name": "Alumni Directory", "short_name": "Directory", "url": "/alumni/", "icons": [{"src": "/static/pwa/icons/icon-96.png", "sizes": "96x96", "type": "image/png"}]},
            {"name": "Job Board", "short_name": "Jobs", "url": "/jobs/", "icons": [{"src": "/static/pwa/icons/icon-96.png", "sizes": "96x96", "type": "image/png"}]},
        ],
    }, content_type="application/manifest+json")
    response["Cache-Control"] = "public, max-age=300"
    return response


@require_GET
def service_worker(request):
    """Worker must be served from /sw.js so it controls the app root.

    It intentionally never renders template or session-specific content.
    """
    worker_path = Path(settings.BASE_DIR) / "static" / "pwa" / "service-worker.js"
    response = HttpResponse(worker_path.read_bytes(), content_type="application/javascript; charset=utf-8")
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Service-Worker-Allowed"] = "/"
    return response
