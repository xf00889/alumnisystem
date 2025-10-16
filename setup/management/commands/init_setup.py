"""
Management command to initialize the setup process.
"""
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import connection
from setup.models import SetupState
from setup.utils import check_environment_setup
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Initialize the setup process'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force initialization even if setup state already exists',
        )
        parser.add_argument(
            '--skip-migrations',
            action='store_true',
            help='Skip running migrations',
        )

    def handle(self, *args, **options):
        self.stdout.write('Initializing setup process...')
        
        # Check if setup state already exists
        if SetupState.objects.exists() and not options['force']:
            self.stdout.write(
                self.style.WARNING('Setup state already exists. Use --force to reinitialize.')
            )
            return

        try:
            # Run migrations if not skipped
            if not options['skip_migrations']:
                self.stdout.write('Running migrations...')
                call_command('migrate', verbosity=0)
                self.stdout.write(self.style.SUCCESS('Migrations completed'))

            # Check environment setup
            self.stdout.write('Checking environment configuration...')
            env_check = check_environment_setup()
            
            if not env_check['complete']:
                self.stdout.write(
                    self.style.WARNING(
                        f'Missing environment variables: {", ".join(env_check["missing_vars"])}'
                    )
                )
            else:
                self.stdout.write(self.style.SUCCESS('Environment configuration is complete'))

            # Create or update setup state
            setup_state, created = SetupState.objects.get_or_create(
                defaults={
                    'is_complete': False,
                    'setup_data': {
                        'environment_check': env_check,
                        'initialization_completed': True
                    }
                }
            )
            
            if not created:
                setup_state.setup_data.update({
                    'environment_check': env_check,
                    'initialization_completed': True
                })
                setup_state.save()

            # Test database connection
            self.stdout.write('Testing database connection...')
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            
            if result:
                self.stdout.write(self.style.SUCCESS('Database connection successful'))
            else:
                raise CommandError('Database connection failed')

            self.stdout.write(
                self.style.SUCCESS('Setup initialization completed successfully!')
            )
            logger.info('Setup initialization completed')

        except Exception as e:
            logger.error(f'Setup initialization failed: {e}')
            raise CommandError(f'Setup initialization failed: {e}')

    def check_database_connection(self):
        """Check if database connection is working."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception:
            return False
