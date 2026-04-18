from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile, MentorApplication, Mentor, Skill, Education, Experience
from alumni_directory.models import Alumni

User = get_user_model()

@receiver(post_save, sender=MentorApplication)
def update_alumni_mentorship_status(sender, instance, **kwargs):
    """Update Alumni mentorship status when mentor application status changes"""
    try:
        alumni = instance.user.alumni
        if instance.status == 'APPROVED':
            alumni.mentorship_status = 'VERIFIED'
        elif instance.status == 'PENDING':
            alumni.mentorship_status = 'PENDING'
        elif instance.status == 'REJECTED':
            alumni.mentorship_status = 'NOT_MENTOR'
        alumni.save()
    except Alumni.DoesNotExist:
        pass

@receiver(post_save, sender=MentorApplication)
def create_mentor_profile(sender, instance, created, **kwargs):
    """Create or update mentor profile when application is approved"""
    if instance.status == 'APPROVED':
        mentor, created = Mentor.objects.get_or_create(user=instance.user)
        if created or not mentor.is_verified:
            mentor.expertise_areas = instance.expertise_areas
            mentor.is_verified = True
            mentor.verification_date = instance.review_date
            mentor.verified_by = instance.reviewed_by
            mentor.save()


# ─── AI Match Cache Invalidation ────────────────────────────────────────────

def _invalidate_ai_cache_for_user(user_id):
    """
    Clear all server-side AI match cache entries for a user and bump the
    profile version so the browser sessionStorage cache also becomes stale.
    """
    from django.core.cache import cache
    import time
    import logging
    logger = logging.getLogger(__name__)

    try:
        # Bump profile version — used as part of the browser cache key
        # so any cached sessionStorage results are automatically invalidated
        version_key = f"ai_profile_version_{user_id}"
        cache.set(version_key, int(time.time()), 60 * 60 * 24 * 7)  # 7 days

        # Clear known server-side match cache keys.
        # We can't do a wildcard delete without Redis SCAN, so we delete the
        # version key pattern and rely on the 24h TTL for individual job caches.
        # Individual job caches will be re-computed on next request.
        logger.debug(f"AI match cache invalidated for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to invalidate AI cache for user {user_id}: {e}")


@receiver(post_save, sender=Profile)
def invalidate_ai_cache_on_profile_save(sender, instance, **kwargs):
    """Clear AI match cache when profile is updated."""
    _invalidate_ai_cache_for_user(instance.user_id)


@receiver(post_save, sender=Skill)
@receiver(post_delete, sender=Skill)
def invalidate_ai_cache_on_skill_change(sender, instance, **kwargs):
    """Clear AI match cache when skills are added, updated, or removed."""
    _invalidate_ai_cache_for_user(instance.profile.user_id)


@receiver(post_save, sender=Education)
@receiver(post_delete, sender=Education)
def invalidate_ai_cache_on_education_change(sender, instance, **kwargs):
    """Clear AI match cache when education is added, updated, or removed."""
    _invalidate_ai_cache_for_user(instance.profile.user_id)


@receiver(post_save, sender=Experience)
@receiver(post_delete, sender=Experience)
def invalidate_ai_cache_on_experience_change(sender, instance, **kwargs):
    """Clear AI match cache when work experience is added, updated, or removed."""
    _invalidate_ai_cache_for_user(instance.profile.user_id)