"""
Management command to create a superuser with environment variables.
"""
import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import IntegrityError
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser using environment variables (setup version)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username for the superuser (overrides environment variable)',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Email for the superuser (overrides environment variable)',
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password for the superuser (overrides environment variable)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation even if superuser already exists',
        )

    def handle(self, *args, **options):
        # Check if superuser already exists
        if User.objects.filter(is_superuser=True).exists() and not options['force']:
            self.stdout.write(
                self.style.WARNING('Superuser already exists. Use --force to create another one.')
            )
            return

        # Get credentials from environment variables or command line arguments
        username = options.get('username') or os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = options.get('email') or os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = options.get('password') or os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        # Validate required fields
        if not username:
            raise CommandError('Username is required. Set DJANGO_SUPERUSER_USERNAME environment variable or use --username')
        
        if not email:
            raise CommandError('Email is required. Set DJANGO_SUPERUSER_EMAIL environment variable or use --email')
        
        if not password:
            raise CommandError('Password is required. Set DJANGO_SUPERUSER_PASSWORD environment variable or use --password')

        try:
            # Create superuser
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created superuser: {username}')
            )
            logger.info(f'Superuser created: {username}')
            
        except IntegrityError as e:
            if 'username' in str(e).lower():
                raise CommandError(f'Username "{username}" already exists')
            elif 'email' in str(e).lower():
                raise CommandError(f'Email "{email}" already exists')
            else:
                raise CommandError(f'Error creating superuser: {e}')
        except Exception as e:
            raise CommandError(f'Unexpected error creating superuser: {e}')

    def check_user_exists(self, username, email):
        """Check if user with given username or email already exists."""
        if User.objects.filter(username=username).exists():
            return f'Username "{username}" already exists'
        if User.objects.filter(email=email).exists():
            return f'Email "{email}" already exists'
        return None
