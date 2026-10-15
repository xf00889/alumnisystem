"""Opt-in email sign-in verification, using django-allauth's staged login.

The password has already been verified by allauth before this stage exists. An
anonymous request cannot select a user ID, start a challenge, or complete login.
Never use registration OTPs as an authentication factor.
"""
import secrets
import time

from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password, make_password
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit
from allauth.account.authentication import record_authentication
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from allauth.account.stages import LoginStageController
from allauth.mfa.models import Authenticator
from allauth.mfa.stages import AuthenticateStage
from allauth.mfa.utils import is_mfa_enabled
from allauth.account.decorators import reauthentication_required

from accounts.models import EmailLoginMFASettings
from core.email_utils import send_email_with_provider

KEY = 'norsu_email_login_challenge'
MAX_ATTEMPTS = 5
TTL_SECONDS = 600
COOLDOWN = 60


def email_enabled(user):
    return bool(getattr(settings, 'EMAIL_LOGIN_MFA_ROLLOUT', False) and EmailLoginMFASettings.objects.filter(user=user, enabled=True).exists())


def _google_identity_confirms_address(identity, current_email):
    """Match a Google-confirmed email to the current account address.

    The identity comes from the linked social account's stored provider data.
    Never infer verification from an OAuth connection alone; do not accept an
    unrelated address or truthy, non-verification values such as ``'yes'``.
    """
    if not isinstance(identity, dict) or not current_email:
        return False
    claim = identity.get('email_verified', identity.get('verified_email'))
    confirmed = claim is True or (isinstance(claim, str) and claim.strip().lower() == 'true')
    provider_address = identity.get('email')
    return bool(
        confirmed and isinstance(provider_address, str)
        and provider_address.strip().casefold() == current_email.strip().casefold()
    )


def verified_email(user):
    """Verify the *current* registered address, including Google-confirmed identities.

    Google SSO may create an account without the legacy allauth EmailAddress row.
    Only trust an existing linked Google identity if Google's verified claim is
    explicitly true and its email exactly matches the current account email.
    A connected provider by itself does not prove control of a changed email.
    """
    address = (user.email or '').strip()
    if not address or not user.pk:
        return False
    if EmailAddress.objects.filter(
        user=user, email__iexact=address, verified=True,
    ).exists():
        return True
    # A linked Google account is not sufficient on its own: the saved Google
    # identity must contain an explicit verified claim for THIS address.
    return any(
        _google_identity_confirms_address(account.extra_data, address)
        for account in SocialAccount.objects.filter(user=user, provider='google')
    )


class EmailOrAuthenticatorStage(AuthenticateStage):
    # Intentionally uses allauth's same key so its existing TOTP verification
    # form can call stage.exit() and preserve existing account protections.
    key = 'mfa_authenticate'

    def handle(self):
        user = self.login.user
        if is_mfa_enabled(user, [Authenticator.Type.TOTP]):
            return HttpResponseRedirect(reverse('mfa_authenticate')), True
        if email_enabled(user):
            return HttpResponseRedirect(reverse('accounts:login_email_challenge')), True
        return None, True


def _stage(request):
    return LoginStageController.enter(request, EmailOrAuthenticatorStage.key)


def _deliver(request, user):
    now = time.time()
    current = request.session.get(KEY, {})
    if current.get('user') == user.pk and now < current.get('sent_at', 0) + COOLDOWN:
        return False, 'Please wait before requesting another code.'
    code = f'{secrets.randbelow(1000000):06d}'
    target = user.email
    text = ('Use this six-digit code to complete your NORSU Alumni sign-in: '
            f'{code}. It expires in 10 minutes. If you did not sign in, ignore this email.')
    # Do not store code in plaintext or log it. No session state is committed
    # until the email provider accepts the message.
    try:
        accepted = send_email_with_provider(
            'Your NORSU Alumni sign-in code', text, [target],
            fail_silently=False, require_delivery=True,
        )
    except Exception:
        accepted = False
    if not accepted:
        return False, 'Unable to send a sign-in code. Try again later or use your authenticator app.'
    request.session[KEY] = {
        'user': user.pk, 'digest': make_password(code),
        'expires': now + TTL_SECONDS, 'sent_at': now, 'attempts': 0,
    }
    request.session.modified = True
    return True, ''


@never_cache
@ratelimit(key='ip', rate='30/15m', block=True)
def email_login_challenge(request):
    stage = _stage(request)
    if not stage or not email_enabled(stage.login.user) or not verified_email(stage.login.user):
        return redirect('account_login')
    user = stage.login.user
    state = request.session.get(KEY, {})
    notice = ''
    if request.method == 'POST':
        action = request.POST.get('action', 'verify')
        if action == 'resend':
            _, notice = _deliver(request, user)
            if not notice:
                notice = 'A new code has been sent.'
        else:
            code = request.POST.get('code', '').strip()
            # Guard against old codes, stale login stages, and OTP guessing.
            if (state.get('user') != user.pk or time.time() > state.get('expires', 0)
                    or state.get('attempts', MAX_ATTEMPTS) >= MAX_ATTEMPTS):
                notice = 'This code has expired or reached the attempt limit. Request another code.'
            elif len(code) != 6 or not code.isdecimal():
                notice = 'Enter the six-digit code.'
            else:
                state['attempts'] += 1
                request.session[KEY] = state
                request.session.modified = True
                if check_password(code, state.get('digest', '')):
                    request.session.pop(KEY, None)
                    record_authentication(request, 'mfa', type='email')
                    return stage.exit()
                notice = 'Incorrect code. Check the email and try again.'
    elif state.get('user') != user.pk or time.time() >= state.get('expires', 0):
        _, notice = _deliver(request, user)
    has_totp = is_mfa_enabled(user, [Authenticator.Type.TOTP])
    return render(request, 'mfa/email_challenge.html', {
        'notice': notice, 'masked_email': user.email[:2] + '***@' + user.email.rsplit('@', 1)[-1],
        'has_totp': has_totp,
    })


@login_required
@reauthentication_required
@require_POST
@ratelimit(key='user', rate='6/h', block=True)
def email_login_mfa_settings(request):
    if not getattr(settings, 'EMAIL_LOGIN_MFA_ROLLOUT', False):
        return redirect('accounts:security_dashboard')
    user = request.user
    action = request.POST.get('action')
    if action not in ('enable', 'disable'):
        return redirect('accounts:security_dashboard')
    if action == 'enable' and not verified_email(user):
        messages.error(request, 'Verify your registered email before enabling email sign-in verification.')
        return redirect('accounts:security_dashboard')
    state, _ = EmailLoginMFASettings.objects.get_or_create(user=user)
    state.enabled = action == 'enable'
    state.save(update_fields=['enabled', 'updated_at'])
    messages.success(request, 'Email sign-in verification settings updated.')
    return redirect('accounts:security_dashboard')
