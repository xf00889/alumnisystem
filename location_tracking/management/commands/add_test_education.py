from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Profile, Education
from location_tracking.models import LocationData
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Add test education record for users without education data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username to add education for (optional)',
        )

    def handle(self, *args, **options):
        username = options.get('username')
        
        if username:
            try:
                user = User.objects.get(username=username)
                users_to_process = [user]
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User {username} not found')
                )
                return
        else:
            # Get users with active locations but no education
            users_with_locations = User.objects.filter(
                locations__is_active=True
            ).distinct()
            
            users_to_process = []
            for user in users_with_locations:
                if hasattr(user, 'profile'):
                    if not user.profile.education.exists():
                        users_to_process.append(user)
                else:
                    # Create profile first
                    Profile.objects.create(user=user)
                    users_to_process.append(user)
        
        if not users_to_process:
            self.stdout.write(
                self.style.SUCCESS('No users need education records')
            )
            return
        
        for user in users_to_process:
            try:
                with transaction.atomic():
                    # Ensure user has a profile
                    if not hasattr(user, 'profile'):
                        Profile.objects.create(user=user)
                    
                    # Create a test education record
                    education = Education.objects.create(
                        profile=user.profile,
                        program='BSIT',  # Bachelor of Science in Information Technology
                        school='NORSU',  # Negros Oriental State University
                        graduation_year=2020,  # Default graduation year
                        is_primary=True
                    )
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created education record for {user.username} '
                            f'(graduation year: {education.graduation_year})'
                        )
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'Error creating education for {user.username}: {str(e)}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Processed {len(users_to_process)} users'
            )
        )