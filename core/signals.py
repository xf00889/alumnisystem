from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from core.models import Notification

User = get_user_model()


# Announcement Notifications
@receiver(post_save, sender='announcements.Announcement')
def create_announcement_notification(sender, instance, created, **kwargs):
    """Create notifications when new announcements are posted"""
    if created and instance.is_active:
        # Get all users to notify based on target audience
        users_to_notify = []
        
        if instance.target_audience == 'ALL':
            users_to_notify = User.objects.filter(is_active=True)
        elif instance.target_audience == 'RECENT':
            # Get recent graduates (you may need to adjust this logic)
            from alumni_directory.models import Alumni
            recent_year = timezone.now().year - 2  # Last 2 years
            recent_alumni = Alumni.objects.filter(graduation_year__gte=recent_year)
            users_to_notify = [alumni.user for alumni in recent_alumni if alumni.user.is_active]
        
        # Create notifications for each user
        for user in users_to_notify:
            Notification.create_notification(
                recipient=user,
                notification_type='announcement',
                title=f'New Announcement: {instance.title}',
                message=f'A new announcement has been posted: {instance.title[:100]}...' if len(instance.title) > 100 else instance.title,
                content_object=instance,
                action_url=f'/announcements/{instance.id}/'
            )


# Event Notifications
@receiver(post_save, sender='events.Event')
def create_event_notification(sender, instance, created, **kwargs):
    """Create notifications when new events are published"""
    if created and instance.status == 'published':
        # Get all active users
        users_to_notify = User.objects.filter(is_active=True)
        
        # Create notifications for each user
        for user in users_to_notify:
            Notification.create_notification(
                recipient=user,
                notification_type='event',
                title=f'New Event: {instance.title}',
                message=f'A new event has been scheduled: {instance.title}. Date: {instance.start_date.strftime("%B %d, %Y")}',
                content_object=instance,
                action_url=f'/events/{instance.id}/'
            )


# Survey Notifications
@receiver(post_save, sender='surveys.Survey')
def create_survey_notification(sender, instance, created, **kwargs):
    """Create notifications when new surveys are made active"""
    if created and instance.status == 'active':
        # Get all active users
        users_to_notify = User.objects.filter(is_active=True)
        
        # Create notifications for each user
        for user in users_to_notify:
            Notification.create_notification(
                recipient=user,
                notification_type='survey',
                title=f'New Survey: {instance.title}',
                message=f'A new survey is available for you to participate: {instance.title}',
                content_object=instance,
                action_url=f'/surveys/{instance.id}/'
            )


# Job Posting Notifications
@receiver(post_save, sender='jobs.JobPosting')
def create_job_posting_notification(sender, instance, created, **kwargs):
    """Create notifications when new job postings are added"""
    if created and instance.is_active:
        # Get all active users
        users_to_notify = User.objects.filter(is_active=True)
        
        # Create notifications for each user
        for user in users_to_notify:
            Notification.create_notification(
                recipient=user,
                notification_type='job_posting',
                title=f'New Job: {instance.job_title}',
                message=f'A new job opportunity is available: {instance.job_title} at {instance.company_name}',
                content_object=instance,
                action_url=f'/jobs/{instance.slug}/'
            )


# Connection Request Notifications
@receiver(post_save, sender='connections.Connection')
def create_connection_notification(sender, instance, created, **kwargs):
    """Create notifications for connection requests and acceptances"""
    if created and instance.status == 'PENDING':
        # Notify the receiver about the connection request
        Notification.create_notification(
            recipient=instance.receiver,
            sender=instance.requester,
            notification_type='connection_request',
            title='New Connection Request',
            message=f'{instance.requester.get_full_name()} wants to connect with you',
            content_object=instance,
            action_url='/connections/requests/'
        )
    elif not created and instance.status == 'ACCEPTED':
        # Notify the requester that their connection was accepted
        Notification.create_notification(
            recipient=instance.requester,
            sender=instance.receiver,
            notification_type='connection_accepted',
            title='Connection Request Accepted',
            message=f'{instance.receiver.get_full_name()} accepted your connection request',
            content_object=instance,
            action_url=f'/accounts/profile/{instance.receiver.id}/'
        )


# Mentorship Request Notifications
@receiver(post_save, sender='accounts.MentorshipRequest')
def create_mentorship_notification(sender, instance, created, **kwargs):
    """Create notifications for mentorship requests and status changes"""
    if created:
        # Notify the mentor about the new mentorship request
        Notification.create_notification(
            recipient=instance.mentor.user,
            sender=instance.mentee,
            notification_type='mentorship_request',
            title='New Mentorship Request',
            message=f'{instance.mentee.get_full_name()} has requested you as a mentor',
            content_object=instance,
            action_url='/mentorship/requests/'
        )
    elif not created:
        # Handle status changes
        if instance.status == 'APPROVED':
            Notification.create_notification(
                recipient=instance.mentee,
                sender=instance.mentor.user,
                notification_type='mentorship_approved',
                title='Mentorship Request Approved',
                message=f'{instance.mentor.user.get_full_name()} has approved your mentorship request',
                content_object=instance,
                action_url='/mentorship/my-mentorships/'
            )
        elif instance.status == 'REJECTED':
            Notification.create_notification(
                recipient=instance.mentee,
                sender=instance.mentor.user,
                notification_type='mentorship_rejected',
                title='Mentorship Request Declined',
                message=f'{instance.mentor.user.get_full_name()} has declined your mentorship request',
                content_object=instance,
                action_url='/mentorship/find-mentors/'
            )


# Message Notifications (for mentorship conversations)
@receiver(post_save, sender='mentorship.Message')
def create_message_notification(sender, instance, created, **kwargs):
    """Create notifications for new messages in conversations"""
    if created:
        # Get the other participant in the conversation
        other_participant = instance.conversation.get_other_participant(instance.sender)

        if other_participant:
            conversation_type = instance.conversation.conversation_type
            if conversation_type == 'mentorship':
                action_url = f'/mentorship/messages/conversation/{instance.conversation.id}/'
                title = 'New Mentorship Message'
            else:
                # For direct conversations in mentorship app, still use mentorship URL
                action_url = f'/mentorship/messages/conversation/{instance.conversation.id}/'
                title = 'New Message'

            Notification.create_notification(
                recipient=other_participant,
                sender=instance.sender,
                notification_type='new_message',
                title=title,
                message=f'{instance.sender.get_full_name()} sent you a message',
                content_object=instance,
                action_url=action_url
            )


# Direct Conversation Message Notifications
@receiver(post_save, sender='connections.DirectMessage')
def create_direct_message_notification(sender, instance, created, **kwargs):
    """Create notifications for new direct messages"""
    if created:
        # Get all participants except the sender
        participants = instance.conversation.participants.exclude(id=instance.sender.id)

        for participant in participants:
            if instance.conversation.conversation_type == 'group':
                title = f'New message in {instance.conversation.group_name or "Group Chat"}'
                message = f'{instance.sender.get_full_name()} sent a message to the group'
            else:
                title = 'New Message'
                message = f'{instance.sender.get_full_name()} sent you a message'

            # Use the generic conversation URL that will redirect appropriately
            action_url = f'/connections/conversations/{instance.conversation.id}/'

            Notification.create_notification(
                recipient=participant,
                sender=instance.sender,
                notification_type='new_message',
                title=title,
                message=message,
                content_object=instance,
                action_url=action_url
            )
