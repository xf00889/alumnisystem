"""Public, credential-free PWA endpoints. No database access or personal content."""
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET


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
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "background_color": "#f7f5f0",
        "theme_color": "#182744",
        "icons": icons,
        "shortcuts": [
            {"name": "Alumni Directory", "short_name": "Directory", "url": "/alumni/"},
            {"name": "Job Board", "short_name": "Jobs", "url": "/jobs/"},
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
