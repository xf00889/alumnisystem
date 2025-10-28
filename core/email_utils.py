"""
Email utilities for sending emails with dynamic provider configuration
Supports both SMTP and Brevo API providers
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from .smtp_settings import get_smtp_settings, update_django_email_settings
from .brevo_email import send_email_with_brevo, get_brevo_settings
from .render_email_fallback import send_email_with_fallback, is_render_hosting
import logging

logger = logging.getLogger(__name__)

def send_email_with_smtp_config(subject, message, recipient_list, from_email=None, fail_silently=False, html_message=None):
    """
    Send email using SMTP configuration from database if available,
    otherwise fallback to Django settings
    
    Args:
        subject: Email subject
        message: Plain text message
        recipient_list: List of recipient email addresses
        from_email: Sender email address (optional)
        fail_silently: Whether to fail silently on errors
        html_message: HTML version of the message (optional)
    """
    try:
        # Always try to load SMTP settings from database if available
        try:
            update_django_email_settings()
            logger.info("Updated Django email settings from database configuration")
        except Exception as e:
            logger.warning(f"Could not update email settings from database: {str(e)}")
            # Continue with Django settings
        
        # Get the current from_email (either from database or settings)
        smtp_settings = get_smtp_settings()
        if from_email is None:
            from_email = smtp_settings.get('from_email', settings.DEFAULT_FROM_EMAIL)
        
        logger.info(f"Sending email from {from_email} using backend {settings.EMAIL_BACKEND}")
        
        # Use the fallback system for Render hosting
        if is_render_hosting():
            logger.info("Using Render email fallback system")
            return send_email_with_fallback(
                subject=subject,
                message=message,
                recipient_list=recipient_list,
                from_email=from_email,
                fail_silently=fail_silently,
                html_message=html_message
            )
        else:
            # For local development, use normal email sending
            if html_message:
                # Use EmailMultiAlternatives for HTML emails
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=message,
                    from_email=from_email,
                    to=recipient_list,
                )
                email.attach_alternative(html_message, "text/html")
                result = email.send(fail_silently=fail_silently)
            else:
                # Use regular send_mail for plain text emails
                result = send_mail(
                    subject=subject,
                    message=message,
                    from_email=from_email,
                    recipient_list=recipient_list,
                    fail_silently=fail_silently,
                )
            
            logger.info(f"Email sent successfully to {recipient_list} using SMTP config: {smtp_settings.get('host', 'console')}")
            return result
        
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_list}: {str(e)}")
        if not fail_silently:
            raise
        return False

def get_active_email_provider():
    """
    Get the currently active email provider
    """
    try:
        from .models.email_provider import EmailProvider
        provider = EmailProvider.get_active_provider()
        return provider
    except Exception as e:
        logger.error(f"Error getting active email provider: {str(e)}")
        return None

def send_email_with_provider(subject, message, recipient_list, from_email=None, fail_silently=False, html_message=None, provider_type=None):
    """
    Send email using the active email provider or specified provider
    
    Args:
        subject: Email subject
        message: Plain text message
        recipient_list: List of recipient email addresses
        from_email: Sender email address (optional)
        fail_silently: Whether to fail silently on errors
        html_message: HTML version of the message (optional)
        provider_type: Specific provider to use ('smtp' or 'brevo'), if None uses active provider
    """
    try:
        # Determine which provider to use
        if provider_type is None:
            provider = get_active_email_provider()
            if provider:
                provider_type = provider.provider_type
            else:
                # Fallback to SMTP if no provider is configured
                provider_type = 'smtp'
                logger.warning("No active email provider found, falling back to SMTP")
        
        # Send email using the selected provider
        if provider_type == 'brevo':
            logger.info(f"Sending email via Brevo to {recipient_list}")
            result = send_email_with_brevo(
                subject=subject,
                message=message,
                recipient_list=recipient_list,
                from_email=from_email,
                html_message=html_message,
                fail_silently=fail_silently
            )
            
            # Update provider usage statistics
            if result:
                provider = get_active_email_provider()
                if provider:
                    provider.increment_usage()
            
            return result
            
        elif provider_type == 'smtp':
            logger.info(f"Sending email via SMTP to {recipient_list}")
            result = send_email_with_smtp_config(
                subject=subject,
                message=message,
                recipient_list=recipient_list,
                from_email=from_email,
                html_message=html_message,
                fail_silently=fail_silently
            )
            
            # Update provider usage statistics
            if result:
                provider = get_active_email_provider()
                if provider:
                    provider.increment_usage()
            
            return result
            
        else:
            error_msg = f"Unknown email provider: {provider_type}"
            logger.error(error_msg)
            if not fail_silently:
                raise ValueError(error_msg)
            return False
            
    except Exception as e:
        error_msg = f"Failed to send email to {recipient_list}: {str(e)}"
        logger.error(error_msg)
        
        # Record error in provider statistics
        provider = get_active_email_provider()
        if provider:
            provider.record_error(error_msg)
        
        if not fail_silently:
            raise
        return False

def get_current_email_info():
    """
    Get information about the current email configuration being used
    """
    try:
        provider = get_active_email_provider()
        
        if not provider:
            return {
                'provider': 'None',
                'error': 'No active email provider configured'
            }
        
        if provider.provider_type == 'smtp':
            smtp_info = get_current_smtp_info()
            smtp_info['provider'] = 'SMTP'
            return smtp_info
        elif provider.provider_type == 'brevo':
            from .brevo_email import get_current_brevo_info
            return get_current_brevo_info()
        else:
            return {
                'provider': provider.provider_type,
                'error': f'Unknown provider type: {provider.provider_type}'
            }
            
    except Exception as e:
        logger.error(f"Error getting email info: {str(e)}")
        return {
            'provider': 'Unknown',
            'error': str(e)
        }

def get_current_smtp_info():
    """
    Get information about the current SMTP configuration being used
    """
    try:
        smtp_settings = get_smtp_settings()
        return {
            'backend': settings.EMAIL_BACKEND,
            'host': smtp_settings.get('host', 'Not configured'),
            'port': smtp_settings.get('port', 'Not configured'),
            'username': smtp_settings.get('username', 'Not configured'),
            'from_email': smtp_settings.get('from_email', settings.DEFAULT_FROM_EMAIL),
            'use_tls': smtp_settings.get('use_tls', False),
            'use_ssl': smtp_settings.get('use_ssl', False),
        }
    except Exception as e:
        logger.error(f"Error getting SMTP info: {str(e)}")
        return {
            'backend': settings.EMAIL_BACKEND,
            'error': str(e)
        }
