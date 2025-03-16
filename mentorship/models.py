from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from accounts.models import Mentor, MentorshipRequest

User = get_user_model()

class MentorshipMeeting(models.Model):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('RESCHEDULED', 'Rescheduled'),
    ]

    mentorship = models.ForeignKey(MentorshipRequest, on_delete=models.CASCADE, related_name='meetings')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    meeting_date = models.DateTimeField()
    duration = models.IntegerField(default=60, help_text="Duration in minutes")
    meeting_link = models.URLField(blank=True, help_text="Video call or meeting location link")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    notes = models.TextField(blank=True, help_text="Meeting notes and action items")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.meeting_date}"

    class Meta:
        verbose_name = _('Mentorship Meeting')
        verbose_name_plural = _('Mentorship Meetings')
        ordering = ['-meeting_date']

class MentorshipMessage(models.Model):
    mentorship = models.ForeignKey(MentorshipRequest, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_mentorship_messages')
    content = models.TextField()
    attachment = models.FileField(upload_to='mentorship/messages/', blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender.get_full_name()} - {self.created_at}"

    class Meta:
        verbose_name = _('Mentorship Message')
        verbose_name_plural = _('Mentorship Messages')
        ordering = ['created_at']

class MentorshipProgress(models.Model):
    mentorship = models.ForeignKey(MentorshipRequest, on_delete=models.CASCADE, related_name='progress_updates')
    title = models.CharField(max_length=200)
    description = models.TextField()
    completed_items = models.TextField(help_text="JSON list of completed items/milestones", blank=True, null=True)
    next_steps = models.TextField(help_text="Next steps and goals", blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_progress_updates')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Progress Update: {self.title}"

    class Meta:
        verbose_name = _('Mentorship Progress')
        verbose_name_plural = _('Mentorship Progress Updates')
        ordering = ['-created_at']

class MentorshipGoal(models.Model):
    PRIORITY_CHOICES = [
        ('HIGH', 'High Priority'),
        ('MEDIUM', 'Medium Priority'),
        ('LOW', 'Low Priority'),
    ]
    
    STATUS_CHOICES = [
        ('NOT_STARTED', 'Not Started'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('DEFERRED', 'Deferred'),
    ]

    mentorship = models.ForeignKey('accounts.MentorshipRequest', on_delete=models.CASCADE, related_name='mentorship_goals')
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NOT_STARTED')
    target_date = models.DateField(null=True, blank=True)
    completion_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_goals')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

    class Meta:
        verbose_name = _('Mentorship Goal')
        verbose_name_plural = _('Mentorship Goals')
        ordering = ['priority', 'target_date', '-created_at']

class MentorshipMilestone(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACHIEVED', 'Achieved'),
    ]

    goal = models.ForeignKey(MentorshipGoal, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    target_date = models.DateField(null=True, blank=True)
    completion_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.get_status_display()}"

    class Meta:
        verbose_name = _('Mentorship Milestone')
        verbose_name_plural = _('Mentorship Milestones')
        ordering = ['target_date', '-created_at']

class MentorshipSkillProgress(models.Model):
    PROFICIENCY_CHOICES = [
        (1, 'Beginner'),
        (2, 'Intermediate'),
        (3, 'Advanced'),
        (4, 'Expert'),
        (5, 'Master'),
    ]

    mentorship = models.ForeignKey('accounts.MentorshipRequest', on_delete=models.CASCADE, related_name='skill_progress')
    skill_name = models.CharField(max_length=100)
    initial_proficiency = models.IntegerField(choices=PROFICIENCY_CHOICES, default=1)
    current_proficiency = models.IntegerField(choices=PROFICIENCY_CHOICES, default=1)
    target_proficiency = models.IntegerField(choices=PROFICIENCY_CHOICES, default=3)
    notes = models.TextField(blank=True)
    last_assessment_date = models.DateField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.skill_name} - Current: {self.get_current_proficiency_display()}"

    class Meta:
        verbose_name = _('Skill Progress')
        verbose_name_plural = _('Skill Progress')
        ordering = ['-current_proficiency', 'skill_name']
        unique_together = ['mentorship', 'skill_name']

class TimelineMilestone(models.Model):
    """
    Model to track the status of timeline milestones.
    This is different from MentorshipMilestone as it's directly tied to the timeline
    entries created in the timeline form.
    """
    STATUS_CHOICES = [
        ('NOT_STARTED', 'Not Started'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
    ]

    mentorship = models.ForeignKey('accounts.MentorshipRequest', on_delete=models.CASCADE, related_name='timeline_milestone_entries')
    period = models.CharField(max_length=50, help_text="Week/Day period (e.g., '1-2', '3-4')")
    description = models.TextField(help_text="Description of the milestone")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NOT_STARTED')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Timeline Milestone')
        verbose_name_plural = _('Timeline Milestones')
        ordering = ['period', 'created_at']
        unique_together = ['mentorship', 'period', 'description']
    
    def __str__(self):
        return f"Week/Day {self.period}: {self.description} - {self.get_status_display()}"
