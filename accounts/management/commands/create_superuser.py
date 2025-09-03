from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Profile
import os

class Command(BaseCommand):
    help = 'Create superuser if it does not exist'

    def handle(self, *args, **options):
        # Get superuser credentials from environment variables
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@admin.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '123')
        
        # Check if superuser already exists
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(
                self.style.SUCCESS('Superuser already exists. Skipping creation.')
            )
            return
        
        # Check if user with this username already exists
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            if not user.is_superuser:
                # Make existing user a superuser
                user.is_superuser = True
                user.is_staff = True
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Made existing user "{username}" a superuser.')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'User "{username}" is already a superuser.')
                )
        else:
            # Create new superuser
            try:
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Superuser "{username}" created successfully.')
                )
                
                # Create profile if it doesn't exist
                profile, created = Profile.objects.get_or_create(user=user)
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Profile created for superuser "{username}".')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'Profile already exists for superuser "{username}".')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating superuser: {e}')
                )
                raise