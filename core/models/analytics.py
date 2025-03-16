from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from core.models import TimeStampedModel

class UserEngagement(TimeStampedModel):
    """
    Track user engagement with the platform
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

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='engagements')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES, default='login')
    points = models.PositiveIntegerField(default=1, help_text=_("Points earned for this activity"))
    description = models.TextField(blank=True, help_text=_("Optional description of the engagement activity"))
    visit_count = models.IntegerField(default=0)
    total_posts = models.IntegerField(default=0)
    total_comments = models.IntegerField(default=0)
    total_reactions = models.IntegerField(default=0)
    last_activity = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _('User Engagement')
        verbose_name_plural = _('User Engagements')
        ordering = ['-created']

    def __str__(self):
        return f"Engagement for {self.user.get_full_name()}"

class EngagementScore(TimeStampedModel):
    """
    Calculate and store engagement scores for users
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='engagement_score')
    total_points = models.PositiveIntegerField(default=0, help_text=_("Total engagement points earned"))
    level = models.PositiveIntegerField(default=1, help_text=_("User engagement level"))
    last_activity = models.DateTimeField(null=True, blank=True, help_text=_("Timestamp of last engagement activity"))

    class Meta:
        verbose_name = _('Engagement Score')
        verbose_name_plural = _('Engagement Scores')
        ordering = ['-total_points']

    def __str__(self):
        return f"Score for {self.user.get_full_name()}: {self.total_points}"

    def calculate_score(self):
        """Calculate engagement score based on various metrics"""
        engagement = self.user.engagements.last()
        if engagement:
            self.total_points = (
                engagement.visit_count * 0.1 +
                engagement.total_posts * 0.3 +
                engagement.total_comments * 0.2 +
                engagement.total_reactions * 0.1
            )
            self.level = max(1, int(self.total_points / 100))
            self.save() 