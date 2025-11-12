from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

User = get_user_model()


class Notification(models.Model):
    """
    Model to represent notifications for various system events
    Uses Django's ContentType framework to reference different model types
    """
    
    NOTIFICATION_TYPES = [
        # General notifications (for all users)
        ('announcement', _('New Announcement')),
        ('event', _('New Event')),
        ('survey', _('New Survey')),
        ('job_posting', _('New Job Posting')),
        ('connection_request', _('Connection Request')),
        ('connection_accepted', _('Connection Accepted')),
        
        # Mentorship-specific notifications
        ('mentorship_request', _('Mentorship Request')),
        ('mentorship_approved', _('Mentorship Approved')),
        ('mentorship_rejected', _('Mentorship Rejected')),
        ('mentorship_disabled', _('Mentorship Disabled')),
        ('mentorship_reactivation_approved', _('Mentorship Reactivation Approved')),
        ('mentorship_reactivation_rejected', _('Mentorship Reactivation Rejected')),
        
        # Message notifications
        ('new_message', _('New Message')),
        
        # System notifications
        ('system', _('System Notification')),
    ]
    
    # Recipient of the notification
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='alumni_notifications'
    )

    # Optional sender (for user-generated notifications)
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_alumni_notifications',
        null=True,
        blank=True
    )
    
    # Notification type
    notification_type = models.CharField(
        max_length=35,
        choices=NOTIFICATION_TYPES
    )
    
    # Generic foreign key to reference any model
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Notification content
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Notification metadata
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Optional URL for action
    action_url = models.URLField(blank=True, null=True)
    
    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['notification_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.recipient.get_full_name()}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    @classmethod
    def create_notification(cls, recipient, notification_type, title, message, 
                          sender=None, content_object=None, action_url=None):
        """
        Helper method to create notifications
        """
        notification = cls.objects.create(
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            title=title,
            message=message,
            content_object=content_object,
            action_url=action_url
        )
        return notification
    
    @classmethod
    def get_unread_count(cls, user):
        """Get count of unread notifications for a user"""
        return cls.objects.filter(recipient=user, is_read=False).count()
    
    @classmethod
    def mark_all_as_read(cls, user):
        """Mark all notifications as read for a user"""
        cls.objects.filter(recipient=user, is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )


class NotificationPreference(models.Model):
    """
    Model to store user notification preferences
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='alumni_notification_preferences'
    )
    
    # Email notification preferences
    email_announcements = models.BooleanField(default=True)
    email_events = models.BooleanField(default=True)
    email_surveys = models.BooleanField(default=True)
    email_job_postings = models.BooleanField(default=True)
    email_connections = models.BooleanField(default=True)
    email_mentorship = models.BooleanField(default=True)
    email_messages = models.BooleanField(default=True)
    
    # In-app notification preferences
    app_announcements = models.BooleanField(default=True)
    app_events = models.BooleanField(default=True)
    app_surveys = models.BooleanField(default=True)
    app_job_postings = models.BooleanField(default=True)
    app_connections = models.BooleanField(default=True)
    app_mentorship = models.BooleanField(default=True)
    app_messages = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Notification Preference')
        verbose_name_plural = _('Notification Preferences')
    
    def __str__(self):
        return f"Notification preferences for {self.user.get_full_name()}"
