"""Mirror mentorship activity into the mentor circle without exposing private notes."""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from accounts.models import MentorshipRequest
from .models import MentorshipProgress, MentorCircleEntry, MentorshipMeeting


@receiver(pre_save, sender=MentorshipRequest, dispatch_uid='mentorship_circle_capture_before')
def capture_before_update(sender, instance, **kwargs):
    instance._mentor_circle_previous = None
    if instance.pk:
        instance._mentor_circle_previous = sender.objects.filter(pk=instance.pk).values(
            'timeline_milestones', 'progress_percentage', 'status'
        ).first()


@receiver(post_save, sender=MentorshipRequest, dispatch_uid='mentorship_circle_activity_on_update')
def record_request_activity(sender, instance, created, **kwargs):
    previous = getattr(instance, '_mentor_circle_previous', None)
    if created or not previous or instance.status != 'APPROVED':
        return
    if previous['timeline_milestones'] != instance.timeline_milestones:
        MentorCircleEntry.objects.create(
            mentor=instance.mentor, mentorship=instance, kind='TIMELINE',
            title='Personal timeline updated',
            body=instance.timeline_milestones[:4000] or 'The timeline has been cleared.',
        )
    if previous['progress_percentage'] != instance.progress_percentage:
        MentorCircleEntry.objects.create(
            mentor=instance.mentor, mentorship=instance, kind='PROGRESS',
            title='Personal progress updated',
            body=f'Overall progress: {instance.progress_percentage}%.',
        )


@receiver(post_save, sender=MentorshipProgress, dispatch_uid='mentorship_circle_progress_record')
def record_progress_notes(sender, instance, created, **kwargs):
    if created and instance.mentorship.status == 'APPROVED':
        MentorCircleEntry.objects.create(
            mentor=instance.mentorship.mentor, mentorship=instance.mentorship,
            author=instance.created_by, kind='PROGRESS',
            title=instance.title[:180], body=instance.description[:4000],
        )


@receiver(pre_save, sender=MentorshipMeeting, dispatch_uid='mentor_circle_meeting_before')
def capture_meeting_before(sender, instance, **kwargs):
    instance._mentor_circle_old_status = None
    if instance.pk:
        instance._mentor_circle_old_status = sender.objects.filter(pk=instance.pk).values_list('status', flat=True).first()


@receiver(post_save, sender=MentorshipMeeting, dispatch_uid='mentor_circle_personal_meeting')
def record_personal_meeting(sender, instance, created, **kwargs):
    if instance.mentorship.status != 'APPROVED':
        return
    old_status = getattr(instance, '_mentor_circle_old_status', None)
    if created or old_status != instance.status:
        MentorCircleEntry.objects.create(
            mentor=instance.mentorship.mentor, mentorship=instance.mentorship,
            kind='MEETING', title=f'Personal meeting: {instance.title}',
            body=f'{instance.get_status_display()} · {instance.meeting_date:%b %d, %Y %I:%M %p}',
        )
