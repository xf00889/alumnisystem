"""Same-origin CSRF refresh for long-running forms, such as manual payment proof.

The endpoint is read-only, never exempt from CSRF, and never grants donation access.
"""
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET


@require_GET
@never_cache
@ensure_csrf_cookie
def refresh_csrf_token(request):
    # A fresh masked token paired with Django's CSRF cookie. Exposes no
    # credentials or session data; only same-origin callers can read JSON.
    return JsonResponse({'csrf_token': get_token(request)})
