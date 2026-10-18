"""Server-authoritative cookie consent. No tracking occurs before affirmative consent."""
import secrets
from django.conf import settings
from django.core import signing

CONSENT_COOKIE = 'norsu_privacy_choice'
VISITOR_COOKIE = 'norsu_visitor_id'
PURPOSE = 'norsu-privacy-v1'
CHOICE_MAX_AGE = 180 * 86400
VISITOR_MAX_AGE = 30 * 86400


def analytics_consented(request):
    raw = request.COOKIES.get(CONSENT_COOKIE, '')
    if not raw:
        return False
    try:
        data = signing.loads(raw, salt=PURPOSE, max_age=CHOICE_MAX_AGE)
    except (signing.BadSignature, signing.SignatureExpired, ValueError, TypeError):
        return False
    return data == 'analytics'


def cookie_choice(request):
    raw = request.COOKIES.get(CONSENT_COOKIE, '')
    if not raw:
        return 'unset'
    try:
        data = signing.loads(raw, salt=PURPOSE, max_age=CHOICE_MAX_AGE)
    except (signing.BadSignature, signing.SignatureExpired, ValueError, TypeError):
        return 'unset'
    return data if data in ('analytics', 'necessary') else 'unset'


def visitor_token(request):
    raw = request.COOKIES.get(VISITOR_COOKIE, '')
    try:
        result = signing.loads(raw, salt=PURPOSE + '-visitor', max_age=VISITOR_MAX_AGE)
    except (signing.BadSignature, signing.SignatureExpired, ValueError, TypeError):
        return None
    if isinstance(result, str) and len(result) == 43:
        return result
    return None


def set_private_cookie(response, name, value, age):
    response.set_cookie(name, value, max_age=age, path='/', secure=not settings.DEBUG,
                        httponly=True, samesite='Lax')


def new_visitor_token():
    return secrets.token_urlsafe(32)
