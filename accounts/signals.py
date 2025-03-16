from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile, MentorApplication, Mentor
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