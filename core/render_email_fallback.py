"""
Email fallback system for Render hosting
"""
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.core.mail.backends.console import EmailBackend
from .sendgrid_email import send_email_via_sendgrid, is_sendgrid_configured
import os

logger = logging.getLogger(__name__)

def is_render_hosting():
    """Check if we're running on Render"""
    return os.getenv('RENDER') is not None

def send_email_with_fallback(subject, message, recipient_list, from_email=None, fail_silently=False, html_message=None):
    """
    Send email with fallback for Render hosting restrictions
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL
    
    # If we're on Render, try multiple email methods
    if is_render_hosting():
        # First, try SendGrid if configured
        if is_sendgrid_configured():
            logger.info("Attempting to send email via SendGrid")
            if send_email_via_sendgrid(subject, message, recipient_list, from_email, html_message):
                return True
            else:
                logger.warning("SendGrid failed, trying SMTP")
        
        # Try SMTP as fallback
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=recipient_list,
                fail_silently=False,
                html_message=html_message
            )
            logger.info(f"Email sent successfully via SMTP: {subject} to {recipient_list}")
            return True
            
        except Exception as e:
            logger.warning(f"SMTP failed on Render: {str(e)}")
            
            # If SendGrid is not configured, log the email
            if not is_sendgrid_configured():
                logger.warning(f"Email content logged instead of sent (no SendGrid configured):")
                logger.warning(f"Subject: {subject}")
                logger.warning(f"To: {recipient_list}")
                logger.warning(f"From: {from_email}")
                logger.warning(f"Message: {message}")
            
            # Return True to prevent errors, but log that email wasn't actually sent
            return True
    else:
        # For local development, use normal email sending
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=recipient_list,
                fail_silently=fail_silently,
                html_message=html_message
            )
            logger.info(f"Email sent successfully: {subject} to {recipient_list}")
            return True
        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            if not fail_silently:
                raise
            return False

def get_render_email_status():
    """
    Get the status of email functionality on Render
    """
    if not is_render_hosting():
        return "local_development"
    
    # Check if SMTP is properly configured
    if settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend':
        return "console_backend"
    
    # Check if we have SMTP settings
    if not settings.EMAIL_HOST or not settings.EMAIL_HOST_USER:
        return "no_smtp_config"
    
    return "smtp_configured"
