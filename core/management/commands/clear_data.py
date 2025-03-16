from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from alumni_directory.models import Alumni, CareerPath, Achievement
from alumni_groups.models import AlumniGroup
from events.models import Event, EventRSVP
from announcements.models import Announcement
from feedback.models import Feedback
from core.models import UserEngagement, EngagementScore, Post, Comment, Reaction
from jobs.models import JobPosting

User = get_user_model()

class Command(BaseCommand):
    help = 'Clears all data from the database while preserving superuser accounts'

    def handle(self, *args, **kwargs):
        self.stdout.write('Clearing all data from the database...')

        try:
            with transaction.atomic():
                # Delete data in a specific order to handle dependencies
                self.stdout.write('Deleting engagement data...')
                Reaction.objects.all().delete()
                Comment.objects.all().delete()
                Post.objects.all().delete()
                UserEngagement.objects.all().delete()
                EngagementScore.objects.all().delete()

                self.stdout.write('Deleting event data...')
                EventRSVP.objects.all().delete()
                Event.objects.all().delete()

                self.stdout.write('Deleting group data...')
                AlumniGroup.objects.all().delete()

                self.stdout.write('Deleting job data...')
                JobPosting.objects.all().delete()

                self.stdout.write('Deleting feedback data...')
                Feedback.objects.all().delete()

                self.stdout.write('Deleting announcement data...')
                Announcement.objects.all().delete()

                self.stdout.write('Deleting alumni data...')
                Achievement.objects.all().delete()
                CareerPath.objects.all().delete()
                Alumni.objects.all().delete()

                self.stdout.write('Deleting user accounts (preserving superusers)...')
                User.objects.exclude(is_superuser=True).delete()

            self.stdout.write(self.style.SUCCESS('Successfully cleared all data while preserving superuser accounts'))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'An error occurred while clearing data: {str(e)}')
            ) 