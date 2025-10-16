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
            
            # Check if the SMTP config table exists
            with connection.cursor() as cursor:
                cursor.execute("SHOW TABLES LIKE 'core_smtpconfig'")
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
                    # No active config, ensure console backend
                    from django.conf import settings
                    settings.EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
                    logger.info("No active SMTP configuration found, using console backend")
            else:
                logger.info("SMTP config table not found, skipping database settings load")
            
        except Exception as e:
            logger.warning(f"Could not load SMTP settings on startup: {str(e)}")
            # Ensure console backend on any error
            from django.conf import settings
            settings.EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'