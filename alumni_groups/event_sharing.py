"""Event-to-group invitation lifecycle. Event Management owns selections; group admins own publishing."""
import re
from django.db import transaction
from django.utils import timezone
from django.utils.html import strip_tags
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from core.models.notifications import Notification
from .models import GroupEventShareRequest, GroupMembership, GroupNotification, Post


def notify_group_admins(share):
    """Send one in-app notice per active group admin, never to ordinary members."""
    group = share.group
    admins = GroupMembership.objects.filter(
        group=group, status='APPROVED', is_active=True, role='ADMIN'
    ).select_related('user')
    target = reverse('alumni_groups:group_detail', kwargs={'slug': group.slug}) + '?tab=notifications'
    title = f'Group event needs review: {share.event.title[:140]}'
    for membership in admins:
        group_notice, group_notice_created = GroupNotification.objects.get_or_create(
            group=group, recipient=membership.user, event_share_request=share,
            defaults={'actor':share.event.created_by, 'message':f'Event "{share.event.title[:125]}" is ready to review. Share or pin it in your group.'},
        )
        if not group_notice_created:
            group_notice.is_read = False
            group_notice.save(update_fields=['is_read'])
        system_notice, system_notice_created = Notification.objects.get_or_create(
            recipient=membership.user,
            notification_type='event',
            content_type=ContentType.objects.get_for_model(share),
            object_id=share.pk,
            defaults={'sender':share.event.created_by, 'title':title,
                      'message':f'Review the event selected for {group.name}. Only a group administrator can publish it to the group.',
                      'action_url':target},
        )
        if not system_notice_created:
            system_notice.is_read = False
            system_notice.read_at = None
            system_notice.save(update_fields=['is_read', 'read_at'])


def queue_event_for_groups(event, group_ids=None):
    """Idempotently queue published events. Called for staff/public/admin event forms."""
    if event.status != 'published' or event.end_date < timezone.now():
        withdraw_event_from_groups(event)
        return
    selected = event.notified_groups.filter(is_active=True)
    if group_ids is not None:
        selected = selected.filter(pk__in=group_ids)
    for group in selected:
        share, created = GroupEventShareRequest.objects.get_or_create(event=event, group=group)
        if share.status == 'WITHDRAWN' and not share.post_id:
            share.status = 'PENDING'
            share.handled_at = None
            share.handled_by = None
            share.save(update_fields=['status', 'handled_at', 'handled_by'])
            created = True
        if created:
            notify_group_admins(share)


def withdraw_event_from_groups(event, group_ids=None):
    """Withdraw invitations and unlink posts from cancelled/deselected events.

    A previously promoted post must not continue advertising a withdrawn event.
    Keep old posts (hidden from the feed) as a moderation/audit record.
    """
    with transaction.atomic():
        affected = GroupEventShareRequest.objects.select_for_update().filter(
            event=event, status__in=('PENDING', 'SHARED', 'PINNED')
        )
        if group_ids is not None:
            affected = affected.filter(group_id__in=group_ids)
        share_ids = []
        for share in affected:
            if share.post_id:
                Post.objects.filter(pk=share.post_id).update(status='REJECTED', is_pinned=False)
                share.post = None
            share.status = 'WITHDRAWN'
            share.handled_by = None
            share.handled_at = None
            share.save(update_fields=['post', 'status', 'handled_by', 'handled_at'])
            share_ids.append(share.pk)
        if not share_ids:
            return
        GroupNotification.objects.filter(event_share_request_id__in=share_ids).update(is_read=True)
        Notification.objects.filter(
            content_type=ContentType.objects.get_for_model(GroupEventShareRequest),
            object_id__in=share_ids,
        ).update(is_read=True, read_at=timezone.now())


def event_post_text(event):
    clean = re.sub(r'\s+', ' ', strip_tags(event.description or '')).strip()[:1600]
    when_date = timezone.localtime(event.start_date) if timezone.is_aware(event.start_date) else event.start_date
    when = when_date.strftime('%b %d, %Y · %I:%M %p')
    return (f'📅 {event.title}\nWhen: {when}\nWhere: {event.location}\n\n'
            f'{clean}\n\nSee event details and RSVP using the link below.')[:5000]


def handle_share_request(share, actor, action):
    """Called while the request row is locked inside transaction.atomic()."""
    if share.status != 'PENDING' or share.post_id:
        return False
    if action in ('share', 'pin'):
        post = Post.objects.create(
            group=share.group, author=actor, content=event_post_text(share.event),
            status='APPROVED', approved_by=actor, approved_at=timezone.now(),
            is_pinned=(action == 'pin'),
        )
        share.post = post
        share.status = 'PINNED' if action == 'pin' else 'SHARED'
    else:
        share.status = 'DISMISSED'
    share.handled_by = actor
    share.handled_at = timezone.now()
    share.save(update_fields=['post', 'status', 'handled_by', 'handled_at'])
    GroupNotification.objects.filter(event_share_request=share).update(is_read=True)
    Notification.objects.filter(
        content_type=ContentType.objects.get_for_model(share), object_id=share.pk
    ).update(is_read=True, read_at=timezone.now())
    return True
