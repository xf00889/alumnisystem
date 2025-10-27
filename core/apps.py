"""
Core app configuration
"""
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Core System'
    
    def ready(self):
        """
        Called when the app is ready
        """
        try:
            # Import here to avoid circular imports
            from django.db import connection
            
            # Check if the SMTP config table exists (database-agnostic)
            with connection.cursor() as cursor:
                if connection.vendor == 'postgresql':
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = 'core_smtpconfig'
                        );
                    """)
                    table_exists = cursor.fetchone()[0]
                elif connection.vendor == 'mysql':
                    cursor.execute("SHOW TABLES LIKE 'core_smtpconfig'")
                    table_exists = cursor.fetchone() is not None
                else:
                    cursor.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name='core_smtpconfig'
                    """)
                    table_exists = cursor.fetchone() is not None
            
            if table_exists:
                # Check if there are any active, verified SMTP configurations
                from .models import SMTPConfig
                active_config = SMTPConfig.objects.filter(is_active=True, is_verified=True).first()
                
                if active_config:
                    from .smtp_settings import update_django_email_settings
                    # Update email settings from database
                    update_django_email_settings()
                else:
                    # No active config, use appropriate backend based on DEBUG setting
                    from django.conf import settings
                    if settings.DEBUG:
                        settings.EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
                        logger.info("No active SMTP configuration found, using console backend for development")
                    else:
                        settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
                        logger.info("No active SMTP configuration found, using SMTP backend for production")
            else:
                logger.info("SMTP config table not found, skipping database settings load")
            
        except Exception as e:
            logger.warning(f"Could not load SMTP settings on startup: {str(e)}")
            # Use appropriate backend based on DEBUG setting
            from django.conf import settings
            if settings.DEBUG:
                settings.EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
                logger.info("Using console backend for development due to error")
            else:
                settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
                logger.info("Using SMTP backend for production despite error")