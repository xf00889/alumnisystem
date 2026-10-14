"""Alumni password management: verified-email, one-time reset links.

The current-password flow remains separate; a reset link never automatically
logs the person in or overrides their authenticator requirement.
"""
import logging

from django.conf import settings
from django.contrib.auth import get_user_model, views as auth_views
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit

from accounts.security import RateLimiter, SecurityAuditLogger
from core.email_utils import send_email_with_provider

logger = logging.getLogger(__name__)
User = get_user_model()


def notify_password_changed(user):
    """Best-effort security notice; never fail the completed password change."""
    if not user.email:
        return
    try:
        send_email_with_provider(
            subject='NORSU Alumni - Your password was changed',
            message=(
                'The password for your NORSU Alumni account has been changed.\n\n'
                'If this was not you, contact the Office of Alumni Affairs immediately '
                'and review your account security.\n'
            ),
            recipient_list=[user.email],
            from_email=settings.DEFAULT_FROM_EMAIL,
            fail_silently=False,
        )
    except Exception:
        logger.exception('Password-change security notice could not be sent')


@never_cache
@sensitive_post_parameters('email')
@ratelimit(key='ip', rate='5/h', method='POST', block=True)
@require_http_methods(['GET', 'POST'])
def request_password_link(request):
    """Send a short-lived Django token only to the account's recorded email.

    Identical response for known/unknown emails prevents enumeration.
    """
    if request.method == 'POST':
        supplied_email = (request.POST.get('email') or '').strip().lower()
        # Signed-in users may not request a link for a different user.
        if request.user.is_authenticated:
            supplied_email = (request.user.email or '').strip().lower()
        if supplied_email and len(supplied_email) <= 254:
            if not RateLimiter.is_rate_limited(supplied_email, 'password_link_request', max_attempts=3, window_minutes=60):
                # Record unknown identities too; don't signal whether an account exists.
                RateLimiter.record_attempt(supplied_email, 'password_link_request', max_attempts=3, window_minutes=60)
                user = User.objects.filter(email__iexact=supplied_email, is_active=True).order_by('pk').first()
                if user and user.email:
                    encoded_id = urlsafe_base64_encode(force_bytes(user.pk))
                    token = default_token_generator.make_token(user)
                    url = request.build_absolute_uri(reverse('accounts:password_recovery_confirm', kwargs={
                        'uidb64': encoded_id, 'token': token,
                    }))
                    message = (
                        'Hello,\n\nUse this link to choose a password for your NORSU Alumni account:\n'
                        + url + '\n\nThis link expires, can be used only until the password changes, '
                        'and will not sign you in automatically. If you did not request this, ignore it.\n'
                    )
                    try:
                        send_email_with_provider(
                            subject='NORSU Alumni - Password recovery link',
                            message=message,
                            recipient_list=[user.email],
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            fail_silently=False,
                        )
                    except Exception:
                        logger.exception('Password recovery email delivery failed')
                    SecurityAuditLogger.log_event('password_link_requested', user=user)
        # No account enumeration, regardless of success or failure.
        return redirect('accounts:password_recovery_requested')
    return render(request, 'accounts/password_recovery_request.html', {
        'recovery_email': request.user.email if request.user.is_authenticated else '',
        'email_locked': request.user.is_authenticated,
    })


@never_cache
@require_http_methods(['GET'])
def password_link_requested(request):
    return render(request, 'accounts/password_recovery_requested.html')


@method_decorator(never_cache, name='dispatch')
class PasswordRecoveryConfirmView(auth_views.PasswordResetConfirmView):
    template_name = 'accounts/password_recovery_confirm.html'
    success_url = reverse_lazy('accounts:password_recovery_complete')
    token_generator = default_token_generator

    def form_valid(self, form):
        user = form.user
        response = super().form_valid(form)
        SecurityAuditLogger.log_event('password_link_completed', user=user)
        notify_password_changed(user)
        # Do not call login() or update_session_auth_hash(): all existing sessions
        # should become invalid due to Django password's session-auth hash.
        return response


@never_cache
@require_http_methods(['GET'])
def password_recovery_complete(request):
    return render(request, 'accounts/password_recovery_complete.html')
