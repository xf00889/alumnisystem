from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError
import os

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a superuser if one does not exist'

    def handle(self, *args, **options):
        # Get superuser credentials from environment variables
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')
        
        try:
            # Check if the specific admin user already exists
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'is_staff': True,
                    'is_superuser': True,
                    'is_active': True,
                }
            )
            
            if created:
                # Set password for newly created user
                user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created superuser: {username}')
                )
            else:
                # Update existing user to ensure it's a superuser with correct credentials
                user.email = email
                user.is_staff = True
                user.is_superuser = True
                user.is_active = True
                user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully updated superuser: {username}')
                )
            
            # Ensure user profile exists
            from accounts.models import UserProfile
            profile, profile_created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'first_name': 'Admin',
                    'last_name': 'User',
                    'phone_number': '+1234567890',
                    'address': 'Admin Address',
                    'city': 'Admin City',
                    'state': 'Admin State',
                    'zip_code': '12345',
                    'country': 'Admin Country',
                }
            )
            
            if profile_created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created profile for superuser: {username}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'Profile already exists for superuser: {username}')
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating/updating superuser: {e}')
            )