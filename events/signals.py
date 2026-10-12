from django.db.models.signals import post_save, pre_delete, m2m_changed
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Event, EventRSVP

User = get_user_model()

@receiver(post_save, sender=Event)
def event_post_save(sender, instance, **kwargs):
    # Also handles draft → published and published → cancelled transitions.
    from alumni_groups.event_sharing import queue_event_for_groups
    queue_event_for_groups(instance)


@receiver(m2m_changed, sender=Event.notified_groups.through)
def event_groups_changed(sender, instance, action, reverse, pk_set, **kwargs):
    if reverse:
        return
    from alumni_groups.event_sharing import queue_event_for_groups, withdraw_event_from_groups
    if action == 'post_add':
        queue_event_for_groups(instance, group_ids=pk_set)
    elif action == 'pre_clear':
        withdraw_event_from_groups(instance)
    elif action == 'post_remove':
        withdraw_event_from_groups(instance, group_ids=pk_set)


@receiver(pre_delete, sender=Event)
def event_pre_delete(sender, instance, **kwargs):
    # Retract shared group posts before the event's requests cascade away.
    from alumni_groups.event_sharing import withdraw_event_from_groups
    withdraw_event_from_groups(instance)


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
    Creates a private notification for the user who made the RSVP.
    """
    message = f"Your RSVP for '{rsvp.event.title}' has been recorded as '{rsvp.get_status_display()}'."
    
    try:
        from core.models.notifications import Notification
        
        # Create a private notification for the user
        Notification.create_notification(
            recipient=rsvp.user,
            notification_type='event',
            title=f"RSVP Confirmation: {rsvp.event.title}",
            message=message,
            content_object=rsvp.event,
            action_url=f'/events/{rsvp.event.pk}/'
        )
    except ImportError:
        # If core.models.notifications is not available, log this
        pass 