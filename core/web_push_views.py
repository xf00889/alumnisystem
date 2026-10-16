"""Authenticated opt-in web push endpoints. CSRF is enforced by Django middleware."""
import json
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from core.models import WebPushSubscription


def _configured():
    return all((settings.WEB_PUSH_VAPID_PUBLIC_KEY, settings.WEB_PUSH_VAPID_PRIVATE_KEY, settings.WEB_PUSH_VAPID_SUBJECT))


def _endpoint_valid(value):
    if not isinstance(value, str) or len(value) > 2048:
        return False
    try:
        u = urlsplit(value)
        host = (u.hostname or '').lower()
        trusted = (host in ('fcm.googleapis.com', 'android.googleapis.com',
                            'updates.push.services.mozilla.com', 'web.push.apple.com')
                   or host.endswith('.notify.windows.com'))
        return u.scheme == 'https' and trusted and not u.username and not u.password and not u.fragment
    except ValueError:
        return False


@never_cache
@login_required
@require_GET
def config(request):
    return JsonResponse({'enabled': _configured(), 'publicKey': settings.WEB_PUSH_VAPID_PUBLIC_KEY if _configured() else ''})


@never_cache
@login_required
@require_POST
def subscribe(request):
    if not _configured():
        return JsonResponse({'error': 'Web push is not configured.'}, status=503)
    if len(request.body) > 8192:
        return JsonResponse({'error': 'Invalid subscription size.'}, status=400)
    try:
        info = json.loads(request.body)
        endpoint = info['endpoint']
        keys = info['keys']
        p256dh, auth = keys['p256dh'], keys['auth']
    except (ValueError, TypeError, KeyError):
        return JsonResponse({'error': 'Invalid subscription.'}, status=400)
    if not (_endpoint_valid(endpoint) and isinstance(p256dh, str) and 20 <= len(p256dh) <= 512
            and isinstance(auth, str) and 8 <= len(auth) <= 256):
        return JsonResponse({'error': 'Invalid subscription parameters.'}, status=400)
    # The browser endpoint is unique to the device; changing account transfers ownership.
    # Old account deliveries are deleted to avoid notifying the wrong person.
    existing = WebPushSubscription.objects.filter(endpoint=endpoint).first()
    if existing:
        if existing.user_id != request.user.pk or existing.p256dh != p256dh or existing.auth != auth:
            existing.deliveries.all().delete()
            existing.user = request.user
            existing.p256dh = p256dh
            existing.auth = auth
            existing.save(update_fields=['user', 'p256dh', 'auth', 'updated_at'])
    else:
        WebPushSubscription.objects.create(user=request.user, endpoint=endpoint, p256dh=p256dh, auth=auth)
    if request.session.get('web_push_endpoint') != endpoint:
        request.session['web_push_endpoint'] = endpoint
    return JsonResponse({'subscribed': True})


@never_cache
@login_required
@require_POST
def unsubscribe(request):
    if len(request.body) > 8192:
        return JsonResponse({'error': 'Invalid subscription size.'}, status=400)
    try:
        endpoint = json.loads(request.body)['endpoint']
    except (ValueError, TypeError, KeyError):
        return JsonResponse({'error': 'Invalid subscription.'}, status=400)
    if not _endpoint_valid(endpoint):
        return JsonResponse({'error': 'Invalid endpoint.'}, status=400)
    WebPushSubscription.objects.filter(user=request.user, endpoint=endpoint).delete()
    if request.session.get('web_push_endpoint') == endpoint:
        request.session.pop('web_push_endpoint', None)
    return JsonResponse({'subscribed': False})
