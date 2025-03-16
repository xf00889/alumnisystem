from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from .models.contact import Address, ContactInfo
from .models.engagement import UserEngagement, EngagementScore

__all__ = [
    'Address',
    'ContactInfo',
    'UserEngagement',
    'EngagementScore'
]

class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    'created' and 'modified' fields.
    """
    created = models.DateTimeField(
        _("Created"),
        auto_now_add=True,
        editable=False,
        help_text=_("The date and time this object was created.")
    )
    modified = models.DateTimeField(
        _("Modified"),
        auto_now=True,
        help_text=_("The date and time this object was last modified.")
    )

    class Meta:
        abstract = True
        ordering = ["-created"]

class UserEngagement(TimeStampedModel):
    """
    Model to track user engagement activities
    """
    ACTIVITY_TYPES = [
        ('login', _('Login')),
        ('profile_update', _('Profile Update')),
        ('group_join', _('Group Join')),
        ('group_post', _('Group Post')),
        ('event_rsvp', _('Event RSVP')),
        ('feedback', _('Feedback Submission')),
        ('document_upload', _('Document Upload')),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='engagements'
    )
    activity_type = models.CharField(
        max_length=20,
        choices=ACTIVITY_TYPES
    )
    points = models.PositiveIntegerField(
        default=1,
        help_text=_("Points earned for this activity")
    )
    description = models.TextField(
        blank=True,
        help_text=_("Optional description of the engagement activity")
    )

    class Meta:
        ordering = ['-created']
        verbose_name = _('User Engagement')
        verbose_name_plural = _('User Engagements')

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_activity_type_display()}"

class EngagementScore(TimeStampedModel):
    """
    Model to track total engagement scores for users
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='engagement_score'
    )
    total_points = models.PositiveIntegerField(
        default=0,
        help_text=_("Total engagement points earned")
    )
    level = models.PositiveIntegerField(
        default=1,
        help_text=_("User engagement level")
    )
    last_activity = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("Timestamp of last engagement activity")
    )

    class Meta:
        ordering = ['-total_points']
        verbose_name = _('Engagement Score')
        verbose_name_plural = _('Engagement Scores')

    def __str__(self):
        return f"{self.user.get_full_name()} - Level {self.level} ({self.total_points} points)" 