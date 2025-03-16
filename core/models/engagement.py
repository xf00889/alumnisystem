from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class UserEngagement(models.Model):
    """
    Track user engagement with the platform
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    last_login = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(auto_now=True)
    visit_count = models.PositiveIntegerField(default=0)
    total_posts = models.PositiveIntegerField(default=0)
    total_comments = models.PositiveIntegerField(default=0)
    total_reactions = models.PositiveIntegerField(default=0)
    
    class Meta:
        verbose_name = _('User Engagement')
        verbose_name_plural = _('User Engagements')
        
    def __str__(self):
        return f"Engagement for {self.user.get_full_name()}"

class EngagementScore(models.Model):
    """
    Calculate and store engagement scores for users
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    score = models.FloatField(default=0.0)
    level = models.PositiveIntegerField(default=1)
    last_calculated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Engagement Score')
        verbose_name_plural = _('Engagement Scores')
        
    def __str__(self):
        return f"Score for {self.user.get_full_name()}: {self.score}"
        
    def calculate_score(self):
        """Calculate engagement score based on various metrics"""
        engagement = self.user.userengagement
        self.score = (
            engagement.visit_count * 0.1 +
            engagement.total_posts * 0.3 +
            engagement.total_comments * 0.2 +
            engagement.total_reactions * 0.1
        )
        self.level = max(1, int(self.score / 100))
        self.save() 