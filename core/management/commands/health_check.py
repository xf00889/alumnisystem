from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
import sys

class Command(BaseCommand):
    help = 'Check application health for debugging 500 errors'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Health Check ==='))
        
        # Check database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            self.stdout.write(self.style.SUCCESS('✓ Database connection: OK'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Database connection: FAILED - {e}'))
            return
        
        # Check settings
        self.stdout.write(f'DEBUG: {settings.DEBUG}')
        self.stdout.write(f'ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}')
        self.stdout.write(f'DATABASE_URL configured: {"DATABASE_URL" in settings.__dict__ or hasattr(settings, "DATABASE_URL")}')
        
        # Check installed apps
        try:
            from django.apps import apps
            apps.check_apps_ready()
            self.stdout.write(self.style.SUCCESS('✓ Apps configuration: OK'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Apps configuration: FAILED - {e}'))
        
        # Check migrations
        try:
            from django.core.management import execute_from_command_line
            from django.db.migrations.executor import MigrationExecutor
            
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            
            if plan:
                self.stdout.write(self.style.WARNING(f'⚠ Pending migrations: {len(plan)}'))
                for migration, backwards in plan:
                    self.stdout.write(f'  - {migration}')
            else:
                self.stdout.write(self.style.SUCCESS('✓ Migrations: Up to date'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Migration check: FAILED - {e}'))
        
        self.stdout.write(self.style.SUCCESS('=== Health Check Complete ==='))