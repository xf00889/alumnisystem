"""
Email utilities for sending emails with dynamic SMTP configuration
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from .smtp_settings import get_smtp_settings, update_django_email_settings
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
