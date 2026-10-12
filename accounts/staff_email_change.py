"""Short-lived account-bound email verification and atomic identity synchronization."""

import logging

from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing
from django.db import transaction
from django.urls import reverse
from django.utils.crypto import salted_hmac

from core.email_utils import send_email_with_provider
from core.models.contact import ContactInfo

from .staff_account_forms import email_is_owned_by_another_user

logger = logging.getLogger(__name__)
TOKEN_SALT = 'accounts.staff.email-change.v1'
TOKEN_MAX_AGE = 30 * 60  # 30 minutes
User = get_user_model()


class InvalidEmailChangeToken(Exception):
    pass


class EmailAlreadyTaken(Exception):
    pass


def _password_binding(user):
    """Do not disclose even a hashed password in the URL token's readable payload."""
    return salted_hmac('staff-email-change-password', user.password).hexdigest()


def create_email_change_token(user, new_email):
    return signing.dumps(
        {'user_id': user.pk, 'old_email': user.email or '',
         'new_email': new_email.lower(), 'password_binding': _password_binding(user)},
        salt=TOKEN_SALT,
    )


def validate_email_change_token(user, token):
    try:
        data = signing.loads(token, salt=TOKEN_SALT, max_age=TOKEN_MAX_AGE)
    except (signing.BadSignature, signing.SignatureExpired) as exc:
        raise InvalidEmailChangeToken('This verification link is invalid or expired.') from exc
    if not isinstance(data, dict):
        raise InvalidEmailChangeToken('This verification link is invalid.')
    if (
        data.get('user_id') != user.pk
        or data.get('old_email') != (user.email or '')
        or data.get('password_binding') != _password_binding(user)
        or not isinstance(data.get('new_email'), str)
        or not data['new_email']
        or data['new_email'] == (user.email or '').lower()
    ):
        raise InvalidEmailChangeToken('This verification link is no longer valid.')
    return data['new_email']


def send_email_change_link(request, user, new_email):
    token = create_email_change_token(user, new_email)
    url = request.build_absolute_uri(
        reverse('accounts:confirm_staff_email', kwargs={'token': token})
    )
    result = send_email_with_provider(
        subject='Confirm your NORSU staff account email change',
        message=(
            f'Hello {user.get_full_name() or user.username},\n\n'
            'A change to the email address on your NORSU staff account was requested.\n'
            f'To confirm the new email address, open this link within 30 minutes:\n{url}\n\n'
            'Your existing email remains active until you confirm. '
            'If you did not request this change, ignore this message and contact the administrator.'
        ),
        recipient_list=[new_email],
        from_email=settings.DEFAULT_FROM_EMAIL,
        fail_silently=False,
    )
    if not result:
        raise RuntimeError('The configured email provider did not accept the verification message.')


def _notify_previous_address(old_email, new_email):
    if not old_email:
        return
    try:
        send_email_with_provider(
            subject='Your NORSU account email address was changed',
            message=(
                'The email address for your NORSU staff account has been changed.\n'
                f'New email: {new_email}\n\n'
                'If you did not make this change, contact the system administrator immediately.'
            ),
            recipient_list=[old_email],
            from_email=settings.DEFAULT_FROM_EMAIL,
            fail_silently=False,
        )
    except Exception:
        # Account update is committed; an alert failure must be logged, not reverse success.
        logger.exception('Failed to notify previous account email after staff email change')


def confirm_email_change(user, token):
    """Revalidate a locked user and update the three identity stores in one transaction."""
    with transaction.atomic():
        locked_user = User.objects.select_for_update().get(pk=user.pk)
        new_email = validate_email_change_token(locked_user, token)
        if email_is_owned_by_another_user(new_email, locked_user.pk):
            raise EmailAlreadyTaken('This email address is no longer available.')
        old_email = locked_user.email or ''

        # Prevent old verified allauth addresses from continuing to work as login aliases.
        identities = EmailAddress.objects.select_for_update().filter(user=locked_user)
        identities.filter(email__iexact=old_email).delete()
        identities.update(primary=False)
        new_identity = identities.filter(email__iexact=new_email).first()
        if new_identity:
            new_identity.email = new_email
            new_identity.primary = True
            new_identity.verified = True
            new_identity.save(update_fields=['email', 'primary', 'verified'])
        else:
            EmailAddress.objects.create(user=locked_user, email=new_email, primary=True, verified=True)

        # Keep existing secondary contact methods unrelated to the old email.
        contact_entries = ContactInfo.objects.select_for_update().filter(
            user=locked_user, contact_type='EMAIL'
        )
        new_contact = contact_entries.filter(contact_value__iexact=new_email).first()
        old_primary = contact_entries.filter(is_primary=True).first()
        contact_entries.update(is_primary=False)
        if new_contact:
            contact = new_contact
            contact_entries.filter(contact_value__iexact=old_email).exclude(pk=contact.pk).delete()
        elif old_primary:
            contact = old_primary
            contact_entries.filter(contact_value__iexact=old_email).exclude(pk=contact.pk).delete()
        else:
            contact = ContactInfo(user=locked_user, contact_type='EMAIL')
            contact_entries.filter(contact_value__iexact=old_email).delete()
        contact.contact_value = new_email
        contact.is_primary = True
        contact.is_verified = True
        contact.save()

        locked_user.email = new_email
        locked_user.save(update_fields=['email'])
        transaction.on_commit(lambda: _notify_previous_address(old_email, new_email))
    return new_email
