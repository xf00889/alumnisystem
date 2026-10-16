"""Deliver durable web push outbox. Run once a minute via systemd timer/cron."""
import logging
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from core.models import WebPushDelivery
from core.web_push import payload_for_notification, notifications_enabled_for_user

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send pending opted-in browser notifications (run via scheduled worker).'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=100)

    def handle(self, *args, **options):
        if not all((settings.WEB_PUSH_VAPID_PRIVATE_KEY, settings.WEB_PUSH_VAPID_PUBLIC_KEY,
                    settings.WEB_PUSH_VAPID_SUBJECT)):
            raise CommandError('Missing VAPID configuration; push delivery remains disabled.')
        try:
            from pywebpush import webpush, WebPushException
        except ImportError as exc:
            raise CommandError('Install pywebpush first: pip install "pywebpush>=2,<3"') from exc
        limit = options['limit']
        if not 1 <= limit <= 1000:
            raise CommandError('Limit must be between 1 and 1000')
        processed = 0
        for _ in range(limit):
            with transaction.atomic():
                # PostgreSQL skip_locked avoids double sending with concurrent workers.
                # No long-lived claim marker that can become stranded on worker crashes.
                due = (WebPushDelivery.objects.select_for_update(skip_locked=True)
                       .select_related('notification', 'subscription')
                       .filter(status='pending', attempts__lt=5)
                       .filter(Q(retry_after__isnull=True) | Q(retry_after__lte=timezone.now()))
                       .order_by('id').first())
                if not due:
                    break
                if not notifications_enabled_for_user(due.notification):
                    due.status = 'failed'
                    due.last_error = 'Disabled in notification preferences'
                    due.save(update_fields=['status', 'last_error'])
                    processed += 1
                    continue
                try:
                    webpush(
                        subscription_info={
                            'endpoint': due.subscription.endpoint,
                            'keys': {'p256dh': due.subscription.p256dh, 'auth': due.subscription.auth},
                        },
                        data=payload_for_notification(due.notification),
                        vapid_private_key=settings.WEB_PUSH_VAPID_PRIVATE_KEY,
                        vapid_claims={'sub': settings.WEB_PUSH_VAPID_SUBJECT},
                        ttl=3600,
                        timeout=8,
                    )
                    due.status = 'sent'
                    due.sent_at = timezone.now()
                    due.last_error = ''
                except WebPushException as exc:
                    status = getattr(getattr(exc, 'response', None), 'status_code', None)
                    due.attempts += 1
                    if status in (404, 410):
                        due.subscription.delete()  # cascades old deliveries
                        processed += 1
                        continue
                    due.last_error = 'Push provider returned an error' + (f' ({status})' if status else '')
                    if due.attempts >= 5 or (status and 400 <= status < 500 and status != 429):
                        due.status = 'failed'
                    else:
                        due.retry_after = timezone.now() + timedelta(minutes=min(60, 2 ** due.attempts))
                    logger.warning('Web push attempt failed for delivery %s (status %s)', due.pk, status)
                except Exception:
                    due.attempts += 1
                    due.last_error = 'Push transport error'
                    if due.attempts >= 5:
                        due.status = 'failed'
                    else:
                        due.retry_after = timezone.now() + timedelta(minutes=min(60, 2 ** due.attempts))
                    logger.exception('Unexpected web push error for delivery %s', due.pk)
                due.save(update_fields=['status', 'attempts', 'retry_after', 'sent_at', 'last_error'])
                processed += 1
        self.stdout.write(f'Processed {processed} browser push deliveries.')
