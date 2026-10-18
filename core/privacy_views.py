"""Cookie consent endpoint; secure, explicit opt-in only."""
from django.core import signing
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from core.privacy_consent import (
    CONSENT_COOKIE,
    VISITOR_COOKIE,
    CHOICE_MAX_AGE,
    VISITOR_MAX_AGE,
    PURPOSE,
    cookie_choice,
    new_visitor_token,
    set_private_cookie,
    visitor_token,
)


@never_cache
@csrf_protect
@ensure_csrf_cookie
@require_http_methods(['GET', 'POST'])
def cookie_consent(request):
    if request.method == 'GET':
        return JsonResponse({
            'choice': cookie_choice(request),
            'version': 1,
            'csrfToken': get_token(request),
        })
    choice = request.POST.get('choice')
    if choice not in ('necessary', 'analytics'):
        return JsonResponse({'error': 'Invalid privacy choice.'}, status=400)
    response = JsonResponse({'choice': choice, 'version': 1})
    signed = signing.dumps(choice, salt=PURPOSE)
    set_private_cookie(response, CONSENT_COOKIE, signed, CHOICE_MAX_AGE)
    if choice == 'analytics':
        existing = visitor_token(request) or new_visitor_token()
        set_private_cookie(
            response,
            VISITOR_COOKIE,
            signing.dumps(existing, salt=PURPOSE + '-visitor'),
            VISITOR_MAX_AGE,
        )
    else:
        response.delete_cookie(VISITOR_COOKIE, path='/', samesite='Lax')
    return response
