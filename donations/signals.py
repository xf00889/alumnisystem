"""Transactional donation notifications for all normal ORM save paths.

Views, staff verification, bulk verification, and Django Admin all call
Donation.save(), so the post_save receiver covers every supported change.
"""
import logging
from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Donation
from .email_utils import (
    send_donation_confirmation_email,
    send_donation_status_update_email,
    send_donation_receipt_email,
)

logger = logging.getLogger(__name__)


def deliver_status_notification(donation_pk, previous_status, expected_status):
    """Notify only when the database still has the committed new status.

    Email delivery failures are logged and never roll back an administrator's
    already-committed verification. A failed provider send can be retried
    operationally; this function does not falsely claim successful delivery.
    """
    try:
        donation = Donation.objects.select_related('campaign', 'donor').get(pk=donation_pk)
        if donation.status != expected_status:
            logger.info('Skipping stale donation email: id=%s expected=%s current=%s',
                        donation_pk, expected_status, donation.status)
            return
        if not (donation.donor.email or donation.donor_email if donation.donor_id else donation.donor_email):
            logger.warning('Donor has no email for donation %s (status=%s); notification not sent',
                           donation_pk, expected_status)
            return
        if previous_status == 'pending_payment' and expected_status == 'pending_verification':
            if not donation.payment_proof or not donation.reference_number:
                logger.error('Donation %s reached verification without saved proof/reference; no acknowledgement sent', donation_pk)
                return
            send_donation_confirmation_email(donation)
        else:
            send_donation_status_update_email(donation, previous_status)
        if expected_status == 'completed' and not donation.receipt_sent:
            send_donation_receipt_email(donation)
    except Donation.DoesNotExist:
        logger.warning('Donation %s removed before email delivery', donation_pk)
    except Exception:
        logger.exception('Donation email delivery failed for donation %s', donation_pk)


@receiver(post_save, sender=Donation, dispatch_uid='donations_status_notifications')
def send_donation_emails(sender, instance, created, **kwargs):
    """Queue status-change notifications after the surrounding transaction commits.

    No email is sent for a newly created unpaid intent or an unchanged status.
    """
    if created:
        logger.info('Donation %s created with status %s; no payment confirmed',
                    instance.pk, instance.status)
        return
    old_status = getattr(instance, '_old_status', None)
    if not old_status or old_status == instance.status:
        return

    donation_pk = instance.pk
    new_status = instance.status
    logger.info('Donation %s status changed %s -> %s (email queued after commit)',
                donation_pk, old_status, new_status)
    transaction.on_commit(
        lambda pk=donation_pk, old=old_status, new=new_status:
        deliver_status_notification(pk, old, new)
    )


@receiver(pre_save, sender=Donation, dispatch_uid='donations_capture_prior_status')
def store_old_status(sender, instance, **kwargs):
    """Detect actual status transitions, including transitions made in Django Admin."""
    if instance.pk:
        instance._old_status = (Donation.objects.filter(pk=instance.pk)
                                .values_list('status', flat=True).first())
    else:
        instance._old_status = None
