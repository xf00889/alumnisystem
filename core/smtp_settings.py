"""
Dynamic SMTP Settings Loader
"""
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
import logging

logger = logging.getLogger(__name__)

def get_smtp_settings():
    """
    Get SMTP settings from database or fallback to Django settings
    """
    try:
        # Try to get from cache first
        smtp_settings = cache.get('smtp_settings')
        
        if smtp_settings is None:
            # Import here to avoid circular imports
            from .models import SMTPConfig
            
            # Get active SMTP configuration
            active_config = SMTPConfig.objects.filter(is_active=True, is_verified=True).first()
            
            if active_config:
                smtp_settings = active_config.get_connection_params()
                # Cache for 1 hour
                cache.set('smtp_settings', smtp_settings, 3600)
                logger.info(f"Loaded SMTP settings from database: {active_config.name}")
            else:
                # Fallback to Django settings
                smtp_settings = {
                    'host': getattr(settings, 'EMAIL_HOST', 'localhost'),
                    'port': getattr(settings, 'EMAIL_PORT', 587),
                    'use_tls': getattr(settings, 'EMAIL_USE_TLS', True),
                    'use_ssl': getattr(settings, 'EMAIL_USE_SSL', False),
                    'username': getattr(settings, 'EMAIL_HOST_USER', ''),
                    'password': getattr(settings, 'EMAIL_HOST_PASSWORD', ''),
                    'from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                }
                logger.warning("No active SMTP configuration found, using Django settings")
        
        return smtp_settings
        
    except Exception as e:
        logger.error(f"Error loading SMTP settings: {str(e)}")
        # Return default settings
        return {
            'host': 'localhost',
            'port': 587,
            'use_tls': True,
            'use_ssl': False,
            'username': '',
            'password': '',
            'from_email': 'noreply@example.com',
        }

def update_django_email_settings():
    """
    Update Django email settings with database configuration
    """
    try:
        smtp_settings = get_smtp_settings()

        # Check if we have valid database settings (not just Django fallback)
        from .models import SMTPConfig
        active_config = SMTPConfig.objects.filter(is_active=True, is_verified=True).first()

        # Check if we're on Render hosting
        import os
        is_render = os.getenv('RENDER') is not None

        if active_config and smtp_settings.get('username') and smtp_settings.get('password'):
            # Update Django settings with database configuration
            settings.EMAIL_HOST = smtp_settings['host']
            settings.EMAIL_PORT = smtp_settings['port']
            settings.EMAIL_USE_TLS = smtp_settings['use_tls']
            settings.EMAIL_USE_SSL = smtp_settings['use_ssl']
            settings.EMAIL_HOST_USER = smtp_settings['username']
            settings.EMAIL_HOST_PASSWORD = smtp_settings['password']
            settings.DEFAULT_FROM_EMAIL = smtp_settings['from_email']

            # On Render, always use console backend to prevent SMTP connection attempts
            if is_render:
                settings.EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
                logger.info("Render hosting detected - using console backend to prevent SMTP connection errors")
            else:
                # For local development, use SMTP backend
                settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
                logger.info("Local development - using SMTP backend")

            logger.info("Django email settings updated from database configuration")
        else:
            # Use console backend for development or if no valid database settings
            if settings.DEBUG:
                settings.EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
                logger.info("Using console backend for development")
            else:
                # For production, try to use Django settings if no database config
                if is_render:
                    # On Render, always use console backend to prevent SMTP connection errors
                    settings.EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
                    logger.info("Render hosting detected - using console backend (no database SMTP config)")
                else:
                    settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
                    logger.info("Using Django settings for production (no database SMTP config)")

    except Exception as e:
        logger.error(f"Error updating Django email settings: {str(e)}")
        # Fallback based on DEBUG setting and Render detection
        import os
        is_render = os.getenv('RENDER') is not None
        
        if settings.DEBUG or is_render:
            settings.EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
            if is_render:
                logger.info("Using console backend for Render hosting due to error")
            else:
                logger.info("Using console backend for development due to error")
        else:
            settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
            logger.info("Using SMTP backend for production despite error")

def clear_smtp_cache():
    """
    Clear SMTP settings cache
    """
    cache.delete('smtp_settings')
    logger.info("SMTP settings cache cleared")

def test_smtp_connection():
    """
    Test SMTP connection using current settings
    """
    try:
        import smtplib
        from email.mime.text import MIMEText
        
        smtp_settings = get_smtp_settings()
        
        # Create SMTP connection
        if smtp_settings['use_ssl']:
            server = smtplib.SMTP_SSL(smtp_settings['host'], smtp_settings['port'])
        else:
            server = smtplib.SMTP(smtp_settings['host'], smtp_settings['port'])
            if smtp_settings['use_tls']:
                server.starttls()
        
        # Authenticate
        if smtp_settings['username'] and smtp_settings['password']:
            server.login(smtp_settings['username'], smtp_settings['password'])
        
        server.quit()
        return True, "Connection successful"
        
    except smtplib.SMTPAuthenticationError as e:
        return False, f"Authentication failed: {str(e)}"
    except smtplib.SMTPConnectError as e:
        return False, f"Connection failed: {str(e)}"
    except Exception as e:
        return False, f"Test failed: {str(e)}"
