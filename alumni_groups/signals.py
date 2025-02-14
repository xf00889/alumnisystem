from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import AlumniGroup, GroupMembership, GroupActivity, GroupAnalytics

@receiver(post_save, sender=AlumniGroup)
def create_group_analytics(sender, instance, created, **kwargs):
    """Create analytics record when a new group is created."""
    if created:
        GroupAnalytics.objects.create(group=instance)

@receiver(post_save, sender=GroupMembership)
def update_group_analytics_on_membership(sender, instance, created, **kwargs):
    """Update group analytics when membership changes."""
    analytics = instance.group.analytics
    analytics.total_members = instance.group.memberships.filter(status='APPROVED').count()
    analytics.active_members = instance.group.memberships.filter(status='APPROVED', is_active=True).count()
    analytics.save()

    if created and instance.status == 'APPROVED':
        GroupActivity.objects.create(
            group=instance.group,
            user=instance.user,
            activity_type='JOIN',
            description=f'{instance.user.get_full_name()} joined the group'
        )

@receiver(post_delete, sender=GroupMembership)
def update_analytics_on_member_leave(sender, instance, **kwargs):
    """Update analytics when a member leaves."""
    try:
        analytics = instance.group.analytics
        analytics.total_members = instance.group.memberships.filter(status='APPROVED').count()
        analytics.active_members = instance.group.memberships.filter(status='APPROVED', is_active=True).count()
        analytics.save()

        GroupActivity.objects.create(
            group=instance.group,
            user=instance.user,
            activity_type='LEAVE',
            description=f'{instance.user.get_full_name()} left the group'
        )
    except (AlumniGroup.DoesNotExist, GroupAnalytics.DoesNotExist):
        pass  # Group might have been deleted 