from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Profile

class Command(BaseCommand):
    help = 'Create missing profiles for existing users'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Creating Missing Profiles ==='))
        
        users_without_profiles = User.objects.filter(profile__isnull=True)
        count = users_without_profiles.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('✓ All users already have profiles'))
            return
        
        self.stdout.write(f'Found {count} users without profiles')
        
        created_count = 0
        for user in users_without_profiles:
            try:
                Profile.objects.create(user=user)
                created_count += 1
                self.stdout.write(f'✓ Created profile for user: {user.username}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Failed to create profile for {user.username}: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {created_count} profiles successfully'))