"""Opt-in aggregate visitor tracking without cookies or request query strings.

IP addresses are personal data. Enable only after privacy disclosure; require
an operational retention schedule. Never trust arbitrary forwarded headers.
"""
import hashlib
import hmac
import ipaddress
import logging
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.db import DatabaseError, IntegrityError
from django.db.models import F
from django.utils import timezone
from core.privacy_consent import (analytics_consented, visitor_token, new_visitor_token,
    set_private_cookie, VISITOR_COOKIE, VISITOR_MAX_AGE, PURPOSE)
from django.core import signing

from core.visitor_analytics_time import visitor_local_date

logger = logging.getLogger(__name__)
SKIP_PREFIXES = (
    '/admin/', '/admin-dashboard/', '/static/', '/media/', '/api/',
    '/health/', '/setup/', '/cdn-cgi/', '/security/', '/accounts/admin/',
)
BOT_MARKERS = ('bot', 'spider', 'crawler', 'slurp', 'headless', 'lighthouse', 'curl/', 'python-requests', 'wget/')


def client_ip(request):
    """Only trust X-Real-IP from an explicitly allowlisted, local reverse proxy.

    Nginx must OVERWRITE X-Real-IP rather than forward client-controlled input.
    Configure its real-IP chain (including Cloudflare CIDRs) separately.
    """
    peer = (request.META.get('REMOTE_ADDR') or '').strip()
    try:
        peer_ip = ipaddress.ip_address(peer)
    except ValueError:
        return None
    candidate = peer
    if peer in getattr(settings, 'VISITOR_TRUSTED_PROXY_IPS', ()):
        candidate = (request.META.get('HTTP_X_REAL_IP') or peer).strip()
    try:
        addr = ipaddress.ip_address(candidate)
    except ValueError:
        return None
    # Do not claim a proxy's loopback as a unique site visitor.
    if addr.is_loopback or addr.is_unspecified or addr.is_multicast:
        return None
    return str(addr)


class VisitorAnalyticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not getattr(settings, 'VISITOR_ANALYTICS_ENABLED', False) or not analytics_consented(request):
            return response
        path = request.path
        if (request.method != 'GET' or response.status_code != 200
                or not response.get('Content-Type', '').lower().startswith('text/html')
                or any(path.startswith(prefix) for prefix in SKIP_PREFIXES)
                or request.META.get('HTTP_DNT') == '1'
                or request.META.get('HTTP_SEC_GPC') == '1'
                or request.META.get('HTTP_HX_REQUEST') == 'true'
                or 'prefetch' in (request.META.get('HTTP_SEC_PURPOSE', '') + request.META.get('HTTP_PURPOSE', '')).lower()
                or any(marker in request.META.get('HTTP_USER_AGENT', '').lower() for marker in BOT_MARKERS)):
            return response
        ip = client_ip(request)
        if not ip:
            return response
        token = visitor_token(request)
        if not token:
            # Consent still valid but browser ID cookie has expired or been cleared.
            # Renew without user action, only while affirmative analytics consent holds.
            token = new_visitor_token()
            set_private_cookie(response, VISITOR_COOKIE,
                               signing.dumps(token, salt=PURPOSE + '-visitor'), VISITOR_MAX_AGE)
        now = timezone.now()
        day = visitor_local_date()
        # This is a sampled hit counter, not an exact request count.
        digest = hmac.new(settings.SECRET_KEY.encode(), f'{day}:{ip}'.encode(), hashlib.sha256).hexdigest()
        key = f'norsu:visitor:{digest}'
        try:
            if not cache.add(key, True, timeout=300):
                return response
        except Exception:
            pass  # Cache outage must never break site navigation.
        try:
            from core.models.visitor_analytics import DailyVisitor, DailyBrowserVisit
            # Do not persist visitor identifier; use a stable keyed hash instead.
            browser_digest = hmac.new(settings.SECRET_KEY.encode(), token.encode(), hashlib.sha256).hexdigest()
            browser, is_new = DailyBrowserVisit.objects.get_or_create(
                day=day, visitor_key=browser_digest,
                defaults={'first_seen': now, 'last_seen': now, 'sampled_page_loads': 1},
            )
            if not is_new:
                DailyBrowserVisit.objects.filter(pk=browser.pk).update(
                    last_seen=now, sampled_page_loads=F('sampled_page_loads') + 1,
                )
            visitor, created = DailyVisitor.objects.get_or_create(
                day=day, ip_address=ip,
                defaults={'first_seen': now, 'last_seen': now, 'sampled_page_loads': 1},
            )
            if not created:
                DailyVisitor.objects.filter(pk=visitor.pk).update(
                    last_seen=now, sampled_page_loads=F('sampled_page_loads') + 1,
                )
        except (DatabaseError, IntegrityError):
            logger.warning('Visitor analytics unavailable; page served normally', exc_info=True)
        return response
