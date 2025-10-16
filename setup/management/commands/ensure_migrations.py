"""
Management command to ensure all migrations are applied.
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Ensure all migrations are applied and database is ready'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force migration even if database appears ready',
        )

    def handle(self, *args, **options):
        self.stdout.write('Ensuring database migrations are applied...')
        
        try:
            # Check if we can connect to the database
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
            
            if not result:
                raise Exception("Database connection failed")
            
            self.stdout.write(self.style.SUCCESS('Database connection successful'))
            
            # Run migrations
            self.stdout.write('Running migrations...')
            call_command('migrate', verbosity=2, interactive=False)
            self.stdout.write(self.style.SUCCESS('Migrations completed'))
            
            # Check if django_session table exists
            with connection.cursor() as cursor:
                if connection.vendor == 'postgresql':
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'django_session'
                        );
                    """)
                elif connection.vendor == 'mysql':
                    cursor.execute("SHOW TABLES LIKE 'django_session'")
                else:
                    cursor.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name='django_session'
                    """)
                session_table_exists = cursor.fetchone() is not None
            
            if session_table_exists:
                self.stdout.write(self.style.SUCCESS('django_session table exists'))
            else:
                self.stdout.write(self.style.WARNING('django_session table not found'))
                # Try to run migrations again
                call_command('migrate', verbosity=2, interactive=False)
            
            # Run system checks
            self.stdout.write('Running system checks...')
            call_command('check', verbosity=2)
            self.stdout.write(self.style.SUCCESS('System checks passed'))
            
            self.stdout.write(
                self.style.SUCCESS('Database is ready!')
            )
            
        except Exception as e:
            logger.error(f'Database setup failed: {e}')
            self.stdout.write(
                self.style.ERROR(f'Database setup failed: {e}')
            )
            raise
