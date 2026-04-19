"""
Signal handlers for the jobs app.

This module contains signal handlers for automatic model creation and updates.
"""

import importlib.util
import logging

from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from jobs.models import JobPreference, JobPosting, UserJobAIScore
from jobs.ai_global_sort import get_ai_profile_version, get_stale_job_ids_for_jobs, mark_scores_pending

logger = logging.getLogger(__name__)

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


@receiver(user_logged_in, dispatch_uid="enqueue_ai_global_scores_on_login")
def enqueue_ai_global_scores_on_login(sender, request, user, **kwargs):
    """
    Precompute AI scores in background after login so ranking is ready
    even before the jobs page is visited.
    """
    if not user or not user.is_authenticated:
        return
    if user.is_superuser or user.is_staff:
        return
    try:
        profile = getattr(user, "profile", None)
        if profile and (getattr(profile, "is_hr", False) or getattr(profile, "is_alumni_coordinator", False)):
            return
    except Exception:
        pass

    if not importlib.util.find_spec("django_q"):
        return

    try:
        from core.ai_config_utils import is_ai_enabled
        if not is_ai_enabled():
            return
    except Exception:
        return

    throttle_minutes = max(1, int(getattr(settings, "AI_GLOBAL_LOGIN_PREFETCH_THROTTLE_MINUTES", 30)))
    throttle_key = f"ai_global_login_prefetch_{user.id}"
    if cache.get(throttle_key):
        return

    jobs = list(JobPosting.objects.filter(is_active=True).exclude(slug="").order_by("-posted_date"))
    if not jobs:
        cache.set(throttle_key, True, throttle_minutes * 60)
        return

    profile_version = get_ai_profile_version(user.id)
    stale_ids = get_stale_job_ids_for_jobs(user, jobs, profile_version)
    if not stale_ids:
        cache.set(throttle_key, True, throttle_minutes * 60)
        return

    chunk_size = max(1, int(getattr(settings, "AI_GLOBAL_ASYNC_CHUNK_SIZE", 50)))
    max_retries = int(getattr(settings, "AI_GLOBAL_ASYNC_MAX_RETRIES", 2))
    backoff_seconds = float(getattr(settings, "AI_GLOBAL_ASYNC_BACKOFF_SECONDS", 0.5))

    mark_scores_pending(user, stale_ids, profile_version)

    try:
        from django_q.tasks import async_task
    except Exception:
        return

    queued = 0
    for index in range(0, len(stale_ids), chunk_size):
        chunk = stale_ids[index:index + chunk_size]
        async_task(
            "jobs.ai_global_sort_tasks.process_user_ai_scores_for_job_ids",
            user.id,
            chunk,
            profile_version,
            max_retries=max_retries,
            backoff_seconds=backoff_seconds,
        )
        queued += len(chunk)

    logger.info(
        "Queued %s AI global score jobs for user=%s after login.",
        queued,
        user.id,
    )
    cache.set(throttle_key, True, throttle_minutes * 60)
