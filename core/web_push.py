"""Safe browser-push validation, enqueueing, and bounded delivery payloads."""
import json
import logging
from urllib.parse import urlsplit

from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)

# Each original Notification yields at most one push per installed browser.
# Do not push donations, sensitive password activity, or arbitrary system messages.
PUSH_TYPES = frozenset({
    'new_message', 'connection_request', 'connection_accepted',
    'announcement', 'mentorship_request', 'mentorship_approved',
    'mentorship_rejected', 'mentorship_disabled',
    'mentorship_reactivation_approved', 'mentorship_reactivation_rejected',
})
PREFERENCE_FIELDS = {
    'new_message': 'app_messages',
    'announcement': 'app_announcements',
    'connection_request': 'app_connections',
    'connection_accepted': 'app_connections',
}
LABELS = {
    'new_message': 'New message',
    'announcement': 'New alumni announcement',
    'connection_request': 'New connection request',
    'connection_accepted': 'Connection accepted',
}


def notifications_enabled_for_user(notification):
    from core.models import NotificationPreference
    preference = NotificationPreference.objects.filter(user_id=notification.recipient_id).first()
    if preference is None:
        return True
    key = PREFERENCE_FIELDS.get(notification.notification_type)
    if notification.notification_type.startswith('mentorship_'):
        key = 'app_mentorship'
    return bool(getattr(preference, key)) if key else False


def queue_web_push(notification_id):
    """Enqueue after commit; sending is only performed by the worker command."""
    from core.models import Notification, WebPushDelivery, WebPushSubscription
    if not all((settings.WEB_PUSH_VAPID_PUBLIC_KEY, settings.WEB_PUSH_VAPID_PRIVATE_KEY, settings.WEB_PUSH_VAPID_SUBJECT)):
        return
    notification = Notification.objects.filter(pk=notification_id).first()
    if not notification or notification.notification_type not in PUSH_TYPES:
        return
    if not notifications_enabled_for_user(notification):
        return
    subs = WebPushSubscription.objects.filter(user_id=notification.recipient_id).values_list('id', flat=True)
    WebPushDelivery.objects.bulk_create(
        [WebPushDelivery(notification_id=notification.pk, subscription_id=sid) for sid in subs],
        ignore_conflicts=True,
    )


def safe_target_url(url):
    """Only relative same-origin links. Never navigate to supplied external URLs."""
    if not isinstance(url, str) or not url.startswith('/') or url.startswith('//') or '\\' in url:
        return reverse('core:all_notifications')
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in url):
        return reverse('core:all_notifications')
    parsed = urlsplit(url)
    if parsed.scheme or parsed.netloc:
        return reverse('core:all_notifications')
    return url[:1024]


def payload_for_notification(notification):
    # Keep message content, names, and personal data out of OS notification previews.
    return json.dumps({
        'id': str(notification.pk),
        'title': LABELS.get(notification.notification_type, 'Mentorship update'),
        'body': 'Open NORSU Alumni to view your update.',
        'url': safe_target_url(notification.action_url),
    }, separators=(',', ':'))


def queue_published_announcement(announcement_id):
    """Create push-ready notifications only for opted-in, audience-matched alumni.

    Restrict recipients using the same canonical audience query as announcement email.
    Bulk operations avoid per-recipient email/HTTP requests while publishing.
    No push subscription means no extra in-app notifications are created.
    """
    from collections import defaultdict
    from django.contrib.contenttypes.models import ContentType
    from announcements.models import Announcement
    from announcements.audience import announcement_recipients
    from core.models import Notification, NotificationPreference, WebPushDelivery, WebPushSubscription
    if not all((settings.WEB_PUSH_VAPID_PUBLIC_KEY, settings.WEB_PUSH_VAPID_PRIVATE_KEY,
                settings.WEB_PUSH_VAPID_SUBJECT)):
        return
    announcement = Announcement.objects.filter(pk=announcement_id, is_active=True).first()
    if not announcement:
        return
    allowed_users = announcement_recipients(announcement).values('id')
    subscriptions = defaultdict(list)
    qs = WebPushSubscription.objects.filter(user_id__in=allowed_users).values_list('user_id', 'id')
    for user_id, sub_id in qs.iterator(chunk_size=500):
        subscriptions[user_id].append(sub_id)
    if not subscriptions:
        return
    opted_out = set(NotificationPreference.objects.filter(user_id__in=subscriptions.keys(),
                     app_announcements=False).values_list('user_id', flat=True))
    targeted_ids = [user_id for user_id in subscriptions if user_id not in opted_out]
    if not targeted_ids:
        return
    content_type = ContentType.objects.get_for_model(announcement)
    url = reverse('announcements:announcement-detail', kwargs={'pk': announcement.pk})
    # Publish creates one notification per subscriber; the queue has its own
    # (notification, subscription) uniqueness guarantee for retry safety.
    for start in range(0, len(targeted_ids), 300):
        ids = targeted_ids[start:start + 300]
        notes = Notification.objects.bulk_create([
            Notification(recipient_id=user_id, notification_type='announcement',
                         title='New alumni announcement', message='A new announcement is available.',
                         content_type=content_type, object_id=announcement.pk, action_url=url)
            for user_id in ids
        ], batch_size=300)
        deliveries = [WebPushDelivery(notification_id=note.pk, subscription_id=sub_id)
                      for note in notes for sub_id in subscriptions[note.recipient_id]]
        WebPushDelivery.objects.bulk_create(deliveries, batch_size=500, ignore_conflicts=True)
