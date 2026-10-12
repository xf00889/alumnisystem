"""Backfill review requests for previously selected, still-current published events.

No event is posted automatically; approved group admins receive a review notice.
"""
from django.db import migrations
from django.utils import timezone


def backfill(apps, schema_editor):
    db = schema_editor.connection.alias
    Event = apps.get_model('events', 'Event')
    Share = apps.get_model('alumni_groups', 'GroupEventShareRequest')
    Membership = apps.get_model('alumni_groups', 'GroupMembership')
    GroupNotification = apps.get_model('alumni_groups', 'GroupNotification')
    GlobalNotification = apps.get_model('core', 'Notification')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    ct, _ = ContentType.objects.using(db).get_or_create(
        app_label='alumni_groups', model='groupeventsharerequest'
    )
    upcoming = Event.objects.using(db).filter(status='published', end_date__gte=timezone.now())
    for event in upcoming.iterator(chunk_size=200):
        for group in event.notified_groups.using(db).filter(is_active=True):
            share, created = Share.objects.using(db).get_or_create(
                event_id=event.pk, group_id=group.pk, defaults={'status':'PENDING'}
            )
            if not created or share.status != 'PENDING':
                continue
            admins = Membership.objects.using(db).filter(
                group_id=group.pk, status='APPROVED', is_active=True, role='ADMIN'
            )
            for membership in admins.iterator(chunk_size=200):
                GroupNotification.objects.using(db).get_or_create(
                    group_id=group.pk, recipient_id=membership.user_id,
                    event_share_request_id=share.pk,
                    defaults={
                        'actor_id':event.created_by_id,
                        'message':f'Event "{event.title[:125]}" is ready to review. Share or pin it in your group.'[:240],
                    },
                )
                GlobalNotification.objects.using(db).get_or_create(
                    recipient_id=membership.user_id, notification_type='event',
                    content_type_id=ct.pk, object_id=share.pk,
                    defaults={
                        'sender_id':event.created_by_id,
                        'title':f'Group event needs review: {event.title[:140]}',
                        'message':f'Review the event selected for {group.name}. Only a group administrator can publish it to the group.',
                        'action_url':f'/groups/{group.slug}/?tab=notifications',
                    },
                )


class Migration(migrations.Migration):
    dependencies = [
        ('alumni_groups', '0005_groupeventsharerequest_and_more'),
        ('core', '0002_notificationpreference_notification'),
    ]
    operations = [migrations.RunPython(backfill, migrations.RunPython.noop)]
