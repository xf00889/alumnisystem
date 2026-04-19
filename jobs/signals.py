"""
Signal handlers for the jobs app.

This module contains signal handlers for automatic model creation and updates.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from jobs.models import JobPreference, JobPosting, UserJobAIScore

User = get_user_model()


@receiver(post_save, sender=User, dispatch_uid="create_job_preference_for_user")
def create_job_preference(sender, instance, created, **kwargs):
    """
    Automatically create a JobPreference instance when a new User is created.
    
    This ensures every user has job preferences initialized with default values,
    ready to be configured when they first visit the job board.
    
    Args:
        sender: The User model class
        instance: The User instance that was saved
        created: Boolean indicating if this is a new user
        **kwargs: Additional keyword arguments from the signal
    """
    if created:
        JobPreference.objects.create(user=instance)


@receiver(post_save, sender=JobPosting, dispatch_uid="mark_ai_scores_pending_on_job_update")
def mark_ai_scores_pending_on_job_update(sender, instance, created, **kwargs):
    """
    Mark cached AI scores as pending when a job posting is edited.
    """
    if created:
        return

    UserJobAIScore.objects.filter(
        job=instance,
        status=UserJobAIScore.Status.READY,
    ).update(
        status=UserJobAIScore.Status.PENDING,
    )
