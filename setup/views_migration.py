"""
Migration runner views for manual database setup.
"""
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views import View
from django.core.management import call_command
from django.db import connection
from django.conf import settings
import os

logger = logging.getLogger(__name__)


class MigrationRunnerView(View):
    """View to manually run database migrations."""
    
    def get(self, request):
        """Show migration status and runner page."""
        context = {
            'database_status': self._check_database_status(),
            'migration_status': self._check_migration_status(),
            'tables_status': self._check_tables_status(),
        }
        return render(request, 'setup/migration_runner.html', context)
    
    def post(self, request):
        """Run migrations manually."""
        try:
            # Run migrations
            logger.info("Starting manual migration process...")
            call_command('migrate', verbosity=2, interactive=False)
            
            # Verify tables were created
            if self._check_tables_status()['django_session_exists']:
                messages.success(request, '✅ Migrations completed successfully! Database is now ready.')
                logger.info("Manual migrations completed successfully")
            else:
                messages.warning(request, '⚠️ Migrations ran but some tables may be missing. Please check the logs.')
                logger.warning("Migrations completed but tables verification failed")
            
        except Exception as e:
            error_msg = f'❌ Migration failed: {str(e)}'
            messages.error(request, error_msg)
            logger.error(f"Manual migration failed: {e}")
        
        return redirect('setup:migration_runner')
    
    def _check_database_status(self):
        """Check if database is accessible."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return {
                    'accessible': True,
                    'message': '✅ Database connection successful'
                }
        except Exception as e:
            return {
                'accessible': False,
                'message': f'❌ Database connection failed: {str(e)}'
            }
    
    def _check_migration_status(self):
        """Check migration status."""
        try:
            # This is a simplified check - in production you might want more detailed status
            return {
                'status': 'unknown',
                'message': 'Run migrations to check status'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error checking migration status: {str(e)}'
            }
    
    def _check_tables_status(self):
        """Check if critical tables exist."""
        try:
            with connection.cursor() as cursor:
                # Check django_session table
                if connection.vendor == 'postgresql':
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'django_session'
                        );
                    """)
                    django_session_exists = cursor.fetchone()[0]
                elif connection.vendor == 'mysql':
                    cursor.execute("SHOW TABLES LIKE 'django_session'")
                    django_session_exists = cursor.fetchone() is not None
                else:
                    cursor.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name='django_session'
                    """)
                    django_session_exists = cursor.fetchone() is not None
                
                # Check setup tables
                if connection.vendor == 'postgresql':
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'setup_siteconfiguration'
                        );
                    """)
                    setup_tables_exist = cursor.fetchone()[0]
                elif connection.vendor == 'mysql':
                    cursor.execute("SHOW TABLES LIKE 'setup_siteconfiguration'")
                    setup_tables_exist = cursor.fetchone() is not None
                else:
                    cursor.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name='setup_siteconfiguration'
                    """)
                    setup_tables_exist = cursor.fetchone() is not None
                
                return {
                    'django_session_exists': django_session_exists,
                    'setup_tables_exist': setup_tables_exist,
                    'all_ready': django_session_exists and setup_tables_exist
                }
                
        except Exception as e:
            logger.error(f"Error checking tables status: {e}")
            return {
                'django_session_exists': False,
                'setup_tables_exist': False,
                'all_ready': False,
                'error': str(e)
            }


class DatabaseStatusAPIView(View):
    """API endpoint to check database status."""
    
    def get(self, request):
        """Return database status as JSON."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return JsonResponse({
                    'status': 'success',
                    'database_ready': True,
                    'message': 'Database is accessible'
                })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'database_ready': False,
                'message': str(e)
            }, status=500)
