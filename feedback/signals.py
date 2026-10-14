"""Notify the owner when the public status of a feedback item changes.

Never include internal staff notes, original attachments, or the user's message.
Does not notify when staff only change an internal note/priority.
"""
import logging
from django.db import transaction
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.conf import settings
from .models import Feedback

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Feedback, dispatch_uid='feedback_capture_old_status_for_email')
def capture_previous_feedback_status(sender, instance, **kwargs):
    instance._status_before_save = None
    if instance.pk:
        instance._status_before_save = sender.objects.filter(pk=instance.pk).values_list('status', flat=True).first()


@receiver(post_save, sender=Feedback, dispatch_uid='feedback_notify_status_change_email')
def notify_feedback_status_change(sender, instance, created, **kwargs):
    old_status = getattr(instance, '_status_before_save', None)
    if created or old_status is None or old_status == instance.status or not instance.user_id:
        return
    email = (instance.user.email or '').strip()
    if not email:
        return
    data = {
        'recipient_name': instance.user.get_full_name() or 'Alumni',
        'feedback_id': instance.pk,
        'feedback_subject': instance.subject,
        'new_status': instance.get_status_display(),
    }

    def send_notice():
        from core.email_utils import send_email_with_provider
        text_body = (
            f"Hello {data['recipient_name']},\n\n"
            f"Your feedback '{data['feedback_subject']}' (#{data['feedback_id']}) "
            f"is now {data['new_status']}.\n"
            "Sign in to the NORSU Alumni Portal for details.\n"
        )
        try:
            send_email_with_provider(
                subject='NORSU Alumni - Feedback status update',
                message=text_body,
                recipient_list=[email],
                html_message=render_to_string('emails/feedback_status_update.html', data),
                fail_silently=False,
            )
        except Exception:
            logger.exception('Feedback status update email failed (feedback ID %s)', data['feedback_id'])

    transaction.on_commit(send_notice)
