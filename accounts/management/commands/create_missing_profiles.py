from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Profile

User = get_user_model()

class Command(BaseCommand):
    help = 'Create profiles for users who do not have one'

    def handle(self, *args, **options):
        users_without_profiles = User.objects.filter(profile__isnull=True)
        created_count = 0
        
        for user in users_without_profiles:
            Profile.objects.create(user=user)
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'Created profile for user: {user.username}')
            )
        
        if created_count == 0:
            self.stdout.write(
                self.style.SUCCESS('All users already have profiles.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {created_count} profiles.')
            )