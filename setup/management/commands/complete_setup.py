"""
Management command to complete the setup process.
"""
import os
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.contrib.auth import get_user_model
from setup.models import SetupState
from setup.utils import check_environment_setup
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Complete the setup process'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-superuser',
            action='store_true',
            help='Create superuser during setup completion',
        )
        parser.add_argument(
            '--skip-superuser',
            action='store_true',
            help='Skip superuser creation even if credentials are available',
        )
        parser.add_argument(
            '--setup-data',
            type=str,
            help='JSON string containing setup configuration data',
        )

    def handle(self, *args, **options):
        self.stdout.write('Completing setup process...')
        
        try:
            # Get or create setup state
            setup_state = SetupState.get_setup_state()
            
            if setup_state.is_complete:
                self.stdout.write(
                    self.style.WARNING('Setup is already complete. Use --force to override.')
                )
                return

            # Check environment setup
            self.stdout.write('Verifying environment configuration...')
            env_check = check_environment_setup()
            
            if not env_check['complete']:
                raise CommandError(
                    f'Environment setup incomplete. Missing: {", ".join(env_check["missing_vars"])}'
                )
            
            self.stdout.write(self.style.SUCCESS('Environment configuration verified'))

            # Create superuser if requested and credentials are available
            if options['create_superuser'] and not options['skip_superuser']:
                self.create_superuser_if_available()

            # Collect static files
            self.stdout.write('Collecting static files...')
            call_command('collectstatic', '--noinput', verbosity=0)
            self.stdout.write(self.style.SUCCESS('Static files collected'))

            # Prepare setup data
            setup_data = {
                'environment_check': env_check,
                'completion_timestamp': str(self.get_current_timestamp()),
                'superuser_created': self.check_superuser_exists(),
            }
            
            # Add custom setup data if provided
            if options['setup_data']:
                import json
                try:
                    custom_data = json.loads(options['setup_data'])
                    setup_data.update(custom_data)
                except json.JSONDecodeError:
                    self.stdout.write(
                        self.style.WARNING('Invalid JSON in --setup-data, ignoring')
                    )

            # Mark setup as complete
            setup_state.mark_complete(setup_data)
            
            # Set environment variable to indicate setup completion
            os.environ['SETUP_COMPLETE'] = 'true'
            
            self.stdout.write(
                self.style.SUCCESS('Setup completed successfully!')
            )
            logger.info('Setup completion successful')

        except Exception as e:
            logger.error(f'Setup completion failed: {e}')
            raise CommandError(f'Setup completion failed: {e}')

    def create_superuser_if_available(self):
        """Create superuser if credentials are available in environment."""
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        
        if username and email and password:
            self.stdout.write('Creating superuser...')
            try:
                call_command('setup_superuser', verbosity=0)
                self.stdout.write(self.style.SUCCESS('Superuser created successfully'))
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Failed to create superuser: {e}')
                )
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Superuser credentials not found in environment variables. '
                    'Skipping superuser creation.'
                )
            )

    def check_superuser_exists(self):
        """Check if a superuser exists."""
        return User.objects.filter(is_superuser=True).exists()

    def get_current_timestamp(self):
        """Get current timestamp."""
        from django.utils import timezone
        return timezone.now()
