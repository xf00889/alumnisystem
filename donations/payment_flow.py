"""Donation intent ownership, campaign payment configuration, and recovery."""
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlencode
import logging

from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from .models import GCashConfig

logger = logging.getLogger(__name__)
TOKEN_SALT = 'donations.guest-payment-access.v1'
TOKEN_MAX_AGE = 60 * 60 * 24 * 30
SESSION_KEY = 'guest_donations_owned'


def assert_campaign_accepts_donations(campaign, user):
    now = timezone.now()
    if (campaign.status != 'active' or not campaign.allow_donations or
            (campaign.start_date and campaign.start_date > now) or
            (campaign.end_date and campaign.end_date < now)):
        raise ValidationError('This campaign is not accepting donations at the moment.')
    if campaign.visibility == 'registered_alumni' and not user.is_authenticated:
        raise PermissionDenied('Sign in to donate to this campaign.')


def resolve_recipient(campaign):
    # If explicitly assigned, never switch to a different account silently.
    config = campaign.gcash_config if campaign.gcash_config_id else GCashConfig.get_active_config()
    if not config or not config.is_active or not config.gcash_number or not config.account_name or not config.qr_code_image:
        raise ValidationError('GCash payment details are unavailable for this campaign.')
    return config


def snapshot_recipient(donation, config):
    donation.gcash_account_name = config.account_name
    donation.gcash_account_number = config.gcash_number
    donation.gcash_payment_instructions = config.instructions
    # Copy the QR at creation: subsequent admin account changes cannot rewrite an intent.
    ext = Path(config.qr_code_image.name).suffix.lower()
    if ext not in ('.jpg', '.jpeg', '.png', '.webp'):
        ext = '.png'
    with config.qr_code_image.open('rb') as source:
        donation.gcash_qr_snapshot.save(f'donation-{donation.pk}{ext}', ContentFile(source.read()), save=False)
    donation.save(update_fields=['gcash_account_name', 'gcash_account_number',
                                 'gcash_payment_instructions', 'gcash_qr_snapshot', 'updated_at'])


def grant_guest_access(request, donation):
    owned = request.session.get(SESSION_KEY, [])
    if donation.pk not in owned:
        request.session[SESSION_KEY] = (owned + [donation.pk])[-30:]
        request.session.modified = True


def signed_guest_token(donation):
    return signing.dumps({'pk': donation.pk, 'email': donation.donor_email}, salt=TOKEN_SALT, compress=True)


def claim_guest_token(request, donation):
    # Recovery links carry a token on GET. Proof forms submit a hidden signed
    # claim so an in-progress guest upload survives cache-backed session loss.
    # Never accept an unsigned donation ID as proof of ownership.
    token = request.GET.get('access', '')
    if request.method == 'POST':
        token = request.POST.get('access', '') or token
    if not token or donation.donor_id is not None:
        return False
    try:
        claim = signing.loads(token, salt=TOKEN_SALT, max_age=TOKEN_MAX_AGE)
    except signing.BadSignature:
        return False
    if claim != {'pk': donation.pk, 'email': donation.donor_email}:
        return False
    grant_guest_access(request, donation)
    return True


def assert_donation_access(request, donation):
    if donation.donor_id is not None:
        if request.user.is_authenticated and donation.donor_id == request.user.pk:
            return
        logger.warning('Donation access denied: donation=%s, authenticated=%s, reason=not_owner',
                       donation.pk, bool(request.user.is_authenticated))
        raise PermissionDenied('You cannot access this donation.')
    if donation.pk in request.session.get(SESSION_KEY, []):
        return
    if claim_guest_token(request, donation):
        return
    logger.warning('Donation access denied: donation=%s, authenticated=%s, reason=no_guest_claim',
                   donation.pk, bool(request.user.is_authenticated))
    raise PermissionDenied('You cannot access this donation.')


def payment_display(donation):
    # No global-account fallback for new donations. Older records without snapshots
    # use their campaign's configured account (or historical default if unassigned).
    name, number, instructions = donation.gcash_account_name, donation.gcash_account_number, donation.gcash_payment_instructions
    qr_url = donation.gcash_qr_snapshot.url if donation.gcash_qr_snapshot else ''
    if not name or not number:
        config = donation.campaign.gcash_config if donation.campaign.gcash_config_id else GCashConfig.get_active_config()
        if config:
            name, number, instructions = config.account_name, config.gcash_number, config.instructions
            qr_url = config.qr_code_image.url if config.qr_code_image else ''
    return {'account_name': name, 'gcash_number': number, 'instructions': instructions, 'qr_url': qr_url}


def email_guest_recovery_link(donation, request):
    if not donation.donor_email or donation.donor_id:
        return
    link = request.build_absolute_uri(reverse('donations:payment_instructions', kwargs={'pk': donation.pk}))
    link += '?' + urlencode({'access': signed_guest_token(donation)})
    email = donation.donor_email
    def send():
        try:
            from core.email_utils import send_email_with_provider
            send_email_with_provider(
                subject='Resume your NORSU donation',
                message=(
                    f'Your payment has NOT been collected yet. To continue your donation of PHP {donation.amount} '
                    f'to {donation.campaign.name}, open this private link within 30 days: {link}\n'
                    'Do not share this link. If you did not start this donation, ignore this email.'
                ),
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception:
            logger.exception('Could not email donation recovery link for donation %s', donation.pk)
    transaction.on_commit(send)
