from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Event, EventRSVP

User = get_user_model()

@receiver(post_save, sender=Event)
def event_post_save(sender, instance, created, **kwargs):
    """
    Signal to handle event creation and updates.
    This will be triggered when an event is created or updated.
    """
    if created and instance.status == 'published':
        # When a new event is created and published, notify the groups
        notify_groups(instance)

@receiver(m2m_changed, sender=Event.notified_groups.through)
def event_groups_changed(sender, instance, action, reverse, model, pk_set, **kwargs):
    """
    Signal to handle changes in the notified_groups M2M relationship.
    This will be triggered when groups are added to or removed from an event.
    """
    if action == "post_add" and instance.status == 'published':
        # When groups are added to a published event, notify the new groups
        notify_groups(instance, pk_set)

def notify_groups(event, group_pks=None):
    """
    Helper function to send notifications to group members.
    If group_pks is provided, only notify those specific groups.
    Otherwise, notify all groups associated with the event.
    """
    groups = event.notified_groups.all()
    if group_pks:
        groups = groups.filter(pk__in=group_pks)

    for group in groups:
        # Get all approved members of the group through GroupMembership
        memberships = group.memberships.filter(status='APPROVED', is_active=True)
        
        # Here you would implement your notification logic
        # This could be sending emails, creating notifications in your notification system, etc.
        # For example:
        for membership in memberships:
            create_notification(
                user=membership.user,
                event=event,
                group=group,
                message=f"New event '{event.title}' has been announced for {group.name}."
            )

def create_notification(user, event, group, message):
    """
    Helper function to create a notification for a user.
    Creates an announcement for the event notification.
    """
    try:
        from announcements.models import Announcement
        Announcement.objects.create(
            title=f"New Event: {event.title}",
            content=message,
            priority_level='MEDIUM',
            target_audience='ALL',
            is_active=True,
            date_posted=timezone.now()
        )
    except ImportError:
        # If announcements app is not available, you might want to log this
        pass

@receiver(post_save, sender=EventRSVP)
def rsvp_post_save(sender, instance, created, **kwargs):
    """
    Signal to handle RSVP creation and updates.
    This could be used to send confirmation emails or notifications.
    """
    if created:
        # Send confirmation to the user
        send_rsvp_confirmation(instance)

def send_rsvp_confirmation(rsvp):
    """
    Helper function to send RSVP confirmation.
    Creates an announcement for the RSVP confirmation.
    """
    message = f"Your RSVP for '{rsvp.event.title}' has been recorded as '{rsvp.get_status_display()}'."
    
    try:
        from announcements.models import Announcement
        Announcement.objects.create(
            title=f"RSVP Confirmation: {rsvp.event.title}",
            content=message,
            priority_level='LOW',
            target_audience='ALL',
            is_active=True,
            date_posted=timezone.now()
        )
    except ImportError:
        # If announcements app is not available, you might want to log this
        pass 