"""
Utility functions for setup detection and management.
"""
import os
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def is_setup_complete():
    """
    Check if the application setup is complete.
    Returns True if setup is complete, False otherwise.
    """
    # Check environment variable first (for deployment)
    setup_complete_env = os.environ.get('SETUP_COMPLETE', '').lower()
    if setup_complete_env in ('true', '1', 'yes'):
        return True
    
    # Check database if available
    try:
        from .models import SetupState
        return SetupState.is_setup_complete()
    except Exception:
        # If database is not available, assume setup is not complete
        return False


def get_setup_state():
    """
    Get the current setup state.
    Returns the SetupState instance or None if not available.
    """
    try:
        from .models import SetupState
        return SetupState.get_setup_state()
    except Exception:
        return None


def is_database_available():
    """
    Check if the database is available and migrations have been run.
    """
    try:
        from django.db import connection
        from django.core.management import execute_from_command_line
        from django.core.management.commands.migrate import Command as MigrateCommand
        
        # Try to connect to database
        connection.ensure_connection()
        
        # Check if setup table exists
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='setup_setupstate'
            """)
            table_exists = cursor.fetchone() is not None
            
        return table_exists
    except Exception:
        return False


def get_required_environment_variables():
    """
    Get list of required environment variables for setup.
    """
    return [
        'SECRET_KEY',
        'DATABASE_URL',
        'ALLOWED_HOSTS',
    ]


def check_environment_setup():
    """
    Check if all required environment variables are set.
    Returns dict with status and missing variables.
    """
    required_vars = get_required_environment_variables()
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    return {
        'complete': len(missing_vars) == 0,
        'missing_vars': missing_vars
    }


def get_setup_progress():
    """
    Get the current setup progress.
    Returns a dict with progress information.
    """
    progress = {
        'environment_setup': False,
        'database_available': False,
        'setup_complete': False,
        'overall_progress': 0
    }
    
    # Check environment setup
    env_check = check_environment_setup()
    progress['environment_setup'] = env_check['complete']
    
    # Check database availability
    progress['database_available'] = is_database_available()
    
    # Check setup completion
    progress['setup_complete'] = is_setup_complete()
    
    # Calculate overall progress
    completed_steps = sum([
        progress['environment_setup'],
        progress['database_available'],
        progress['setup_complete']
    ])
    progress['overall_progress'] = (completed_steps / 3) * 100
    
    return progress
