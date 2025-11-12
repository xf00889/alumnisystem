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
        
        # Log email sending attempt with enhanced context
        logger.info(
            f"Sending email via SMTP: Subject={subject}, To={recipient_list}, From={from_email}",
            extra={
                'subject': subject,
                'recipient_list': recipient_list,
                'from_email': from_email,
                'has_html': bool(html_message),
                'smtp_host': smtp_settings.get('host', 'Not configured'),
                'email_backend': settings.EMAIL_BACKEND,
                'action': 'email_send_attempt'
            }
        )
        
        # Use the fallback system for Render hosting
        if is_render_hosting():
            logger.info("Using Render email fallback system")
            result = send_email_with_fallback(
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
        
        if result:
            logger.info(
                f"Email sent successfully via SMTP: Subject={subject}, To={recipient_list}",
                extra={
                    'subject': subject,
                    'recipient_list': recipient_list,
                    'from_email': from_email,
                    'smtp_host': smtp_settings.get('host', 'console'),
                    'action': 'email_sent'
                }
            )
        else:
            logger.warning(
                f"Email send returned False: Subject={subject}, To={recipient_list}",
                extra={
                    'subject': subject,
                    'recipient_list': recipient_list,
                    'from_email': from_email,
                    'action': 'email_send_failed'
                }
            )
        
        return result
        
    except Exception as e:
        logger.error(
            f"Failed to send email via SMTP: Subject={subject}, To={recipient_list}, Error={str(e)}",
            extra={
                'subject': subject,
                'recipient_list': recipient_list,
                'from_email': from_email,
                'error_type': type(e).__name__,
                'action': 'email_send_error'
            },
            exc_info=True
        )
        if not fail_silently:
            raise
        return False

def get_active_email_provider():
    """
    Get the currently active email provider
    If no EmailProvider exists, check for active Brevo or SMTP configs and auto-create provider
    """
    try:
        from .models.email_provider import EmailProvider
        provider = EmailProvider.get_active_provider()
        
        # If no provider exists, check for active configurations and auto-create provider
        if not provider:
            logger.info("No EmailProvider found, checking for active configurations...")
            
            # Check for Brevo config first (preferred for Render)
            from .models.brevo_config import BrevoConfig
            brevo_config = BrevoConfig.objects.filter(is_active=True, is_verified=True).first()
            
            if brevo_config:
                logger.info(f"Found active Brevo config (ID: {brevo_config.id}), auto-creating EmailProvider")
                # Auto-create and activate Brevo provider
                provider, created = EmailProvider.objects.get_or_create(
                    provider_type='brevo',
                    defaults={'is_active': True}
                )
                if not created and not provider.is_active:
                    provider.is_active = True
                    provider.save()
                logger.info(f"EmailProvider for Brevo {'created' if created else 'activated'}")
                return provider
            
            # Check for SMTP config as fallback
            from .models.smtp_config import SMTPConfig
            smtp_config = SMTPConfig.objects.filter(is_active=True, is_verified=True).first()
            
            if smtp_config:
                logger.info(f"Found active SMTP config (ID: {smtp_config.id}), auto-creating EmailProvider")
                # Auto-create and activate SMTP provider
                provider, created = EmailProvider.objects.get_or_create(
                    provider_type='smtp',
                    defaults={'is_active': True}
                )
                if not created and not provider.is_active:
                    provider.is_active = True
                    provider.save()
                logger.info(f"EmailProvider for SMTP {'created' if created else 'activated'}")
                return provider
            
            logger.warning("No active email configuration found (Brevo or SMTP)")
        
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
                logger.info(f"Using email provider: {provider_type}")
            else:
                # Last resort: check Brevo settings directly (for backward compatibility)
                brevo_settings = get_brevo_settings()
                if brevo_settings.get('api_key'):
                    logger.info("No EmailProvider found, but Brevo API key exists. Using Brevo directly.")
                    provider_type = 'brevo'
                else:
                    # Fallback to SMTP if no provider is configured
                    provider_type = 'smtp'
                    logger.warning("No active email provider found, falling back to SMTP")
        
        # Log email sending attempt with provider information
        logger.info(
            f"Sending email via {provider_type.upper()}: Subject={subject}, To={recipient_list}, Provider={provider_type}",
            extra={
                'subject': subject,
                'recipient_list': recipient_list,
                'from_email': from_email,
                'provider_type': provider_type,
                'has_html': bool(html_message),
                'action': 'email_send_attempt'
            }
        )
        
        # Send email using the selected provider
        if provider_type == 'brevo':
            # If from_email is the default placeholder, use Brevo config instead
            # This ensures we use the verified Brevo sender email
            if from_email and (from_email == settings.DEFAULT_FROM_EMAIL or 'example.com' in from_email.lower()):
                brevo_settings = get_brevo_settings()
                if brevo_settings.get('from_email'):
                    logger.info(
                        f"Replacing default from_email '{from_email}' with Brevo config: {brevo_settings.get('from_email')}",
                        extra={
                            'old_from_email': from_email,
                            'new_from_email': brevo_settings.get('from_email'),
                            'action': 'email_provider_config'
                        }
                    )
                    from_email = None  # Let Brevo use its configured email
            
            result = send_email_with_brevo(
                subject=subject,
                message=message,
                recipient_list=recipient_list,
                from_email=from_email,
                html_message=html_message,
                fail_silently=fail_silently
            )
            
            # Log provider switching if needed
            if result:
                provider = get_active_email_provider()
                if provider:
                    provider.increment_usage()
                    logger.info(
                        f"Email sent successfully via Brevo: Subject={subject}, To={recipient_list}",
                        extra={
                            'subject': subject,
                            'recipient_list': recipient_list,
                            'provider_type': 'brevo',
                            'provider_id': provider.id if provider else None,
                            'action': 'email_sent'
                        }
                    )
            else:
                logger.warning(
                    f"Email send failed via Brevo: Subject={subject}, To={recipient_list}",
                    extra={
                        'subject': subject,
                        'recipient_list': recipient_list,
                        'provider_type': 'brevo',
                        'action': 'email_send_failed'
                    }
                )
            
            return result
            
        elif provider_type == 'smtp':
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
                    logger.info(
                        f"Email sent successfully via SMTP: Subject={subject}, To={recipient_list}",
                        extra={
                            'subject': subject,
                            'recipient_list': recipient_list,
                            'provider_type': 'smtp',
                            'provider_id': provider.id if provider else None,
                            'action': 'email_sent'
                        }
                    )
            else:
                logger.warning(
                    f"Email send failed via SMTP: Subject={subject}, To={recipient_list}",
                    extra={
                        'subject': subject,
                        'recipient_list': recipient_list,
                        'provider_type': 'smtp',
                        'action': 'email_send_failed'
                    }
                )
            
            return result
            
        else:
            error_msg = f"Unknown email provider: {provider_type}"
            logger.error(error_msg)
            if not fail_silently:
                raise ValueError(error_msg)
            return False
            
    except Exception as e:
        error_msg = f"Failed to send email to {recipient_list}: {str(e)}"
        logger.error(
            f"Exception sending email: Subject={subject}, To={recipient_list}, Error={str(e)}",
            extra={
                'subject': subject,
                'recipient_list': recipient_list,
                'from_email': from_email,
                'provider_type': provider_type,
                'error_type': type(e).__name__,
                'error_message': str(e),
                'action': 'email_send_exception'
            },
            exc_info=True
        )
        
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
