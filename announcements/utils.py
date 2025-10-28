from django.core.mail import send_mail, get_connection, BadHeaderError
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth import get_user_model
import logging
import socket

logger = logging.getLogger(__name__)
User = get_user_model()

def verify_email_settings():
    """Verify email settings are properly configured"""
    required_settings = [
        'EMAIL_HOST', 'EMAIL_PORT', 'EMAIL_HOST_USER',
        'EMAIL_HOST_PASSWORD', 'DEFAULT_FROM_EMAIL'
    ]
    
    missing_settings = [setting for setting in required_settings 
                       if not hasattr(settings, setting) or not getattr(settings, setting)]
    
    if missing_settings:
        logger.error(f"Missing email settings: {', '.join(missing_settings)}")
        return False
    return True

def send_announcement_notification(announcement, recipient_list=None):
    """
    Send email notification about a new announcement.
    If recipient_list is None, it will send to all active users based on target_audience.
    """
    try:
        logger.info(f"Starting email notification for announcement: {announcement.title}")
        
        # Verify email settings first
        if not verify_email_settings():
            logger.error("Email settings verification failed")
            return False
            
        subject = f'New Announcement: {announcement.title}'
        
        # Prepare HTML content
        context = {
            'announcement': announcement,
            'site_url': settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000'
        }
        logger.debug(f"Email context prepared: {context}")
        
        try:
            html_message = render_to_string('announcements/email/announcement_notification.html', context)
            plain_message = strip_tags(html_message)
            logger.debug("Email templates rendered successfully")
        except Exception as e:
            logger.error(f"Error rendering email templates: {str(e)}", exc_info=True)
            return False
        
        # If no recipient list is provided, get users based on target audience
        if recipient_list is None:
            users = User.objects.filter(is_active=True)
            logger.info(f"Total active users found: {users.count()}")
            
            if announcement.target_audience == 'RECENT':
                users = users.filter(profile__graduation_year__gte=2023)
                logger.info(f"Filtered to recent graduates: {users.count()} users")
            elif announcement.target_audience == 'DEPARTMENT':
                logger.info("Department filtering not implemented yet")
            
            recipient_list = list(users.values_list('email', flat=True))
        
        # Filter out empty email addresses and remove duplicates
        recipient_list = list(filter(None, set(recipient_list)))
        logger.info(f"Final recipient list: {recipient_list}")
        
        # Debug information
        logger.info(f"Preparing to send email to {len(recipient_list)} recipients")
        logger.debug(f"Email settings: HOST={settings.EMAIL_HOST}, PORT={settings.EMAIL_PORT}")
        logger.debug(f"Using email account: {settings.EMAIL_HOST_USER}")
        logger.debug(f"From email: {settings.DEFAULT_FROM_EMAIL}")
        
        if not recipient_list:
            logger.warning("No recipients found for the announcement")
            return False
        
        # Test SMTP connection first
        try:
            # Try to establish a socket connection to the SMTP server
            sock = socket.create_connection((settings.EMAIL_HOST, settings.EMAIL_PORT), timeout=5)
            sock.close()
            logger.info("SMTP server is reachable")
        except Exception as e:
            logger.error(f"Cannot connect to SMTP server: {str(e)}", exc_info=True)
            return False
        
        # Get email connection
        try:
            connection = get_connection(
                host=settings.EMAIL_HOST,
                port=settings.EMAIL_PORT,
                username=settings.EMAIL_HOST_USER,
                password=settings.EMAIL_HOST_PASSWORD,
                use_tls=settings.EMAIL_USE_TLS
            )
            
            # Test the connection
            connection.open()
            logger.info("Successfully established connection to email server")
            
            # Send email using unified email system
            from core.email_utils import send_email_with_provider
            
            success = send_email_with_provider(
                subject=subject,
                message=plain_message,
                recipient_list=recipient_list,
                from_email=settings.DEFAULT_FROM_EMAIL,
                html_message=html_message,
                fail_silently=False
            )
            
            if success:
                logger.info("Email sent successfully")
                return True
            else:
                logger.error("Failed to send email")
                return False
            
        except BadHeaderError as e:
            logger.error(f"Invalid header found in email: {str(e)}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}", exc_info=True)
            return False
        finally:
            try:
                connection.close()
                logger.info("Email connection closed")
            except Exception as e:
                logger.error(f"Error closing email connection: {str(e)}", exc_info=True)
            
    except Exception as e:
        logger.error(f"Unexpected error in send_announcement_notification: {str(e)}", exc_info=True)
        return False 