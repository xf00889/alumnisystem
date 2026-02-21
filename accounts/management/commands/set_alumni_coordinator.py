"""
Management command to set or remove Alumni Coordinator role for users
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from accounts.models import Profile

User = get_user_model()


class Command(BaseCommand):
    help = 'Set or remove Alumni Coordinator role for a user'

    def add_arguments(self, parser):
        parser.add_argument(
            'username',
            type=str,
            help='Username of the user to modify'
        )
        parser.add_argument(
            '--remove',
            action='store_true',
            help='Remove Alumni Coordinator role instead of adding it'
        )

    def handle(self, *args, **options):
        username = options['username']
        remove = options['remove']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'User "{username}" does not exist')

        # Ensure user has a profile
        profile, created = Profile.objects.get_or_create(user=user)

        if remove:
            if not profile.is_alumni_coordinator:
                self.stdout.write(
                    self.style.WARNING(
                        f'User "{username}" is not an Alumni Coordinator'
                    )
                )
                return

            profile.is_alumni_coordinator = False
            profile.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully removed Alumni Coordinator role from user "{username}"'
                )
            )
        else:
            if profile.is_alumni_coordinator:
                self.stdout.write(
                    self.style.WARNING(
                        f'User "{username}" is already an Alumni Coordinator'
                    )
                )
                return

            profile.is_alumni_coordinator = True
            profile.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully set user "{username}" as Alumni Coordinator'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'User can now access admin dashboard but NOT system configuration'
                )
            )
