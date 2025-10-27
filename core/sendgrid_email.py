"""
SendGrid email integration for Render hosting
"""
import logging
import os
from django.conf import settings

logger = logging.getLogger(__name__)

def is_sendgrid_configured():
    """Check if SendGrid is configured"""
    return bool(os.getenv('SENDGRID_API_KEY'))

def send_email_via_sendgrid(subject, message, recipient_list, from_email=None, html_message=None):
    """
    Send email via SendGrid API
    """
    if not is_sendgrid_configured():
        logger.warning("SendGrid not configured, falling back to SMTP")
        return False
    
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail
        
        # Initialize SendGrid client
        sg = sendgrid.SendGridAPIClient(api_key=os.getenv('SENDGRID_API_KEY'))
        
        # Prepare email
        if from_email is None:
            from_email = settings.DEFAULT_FROM_EMAIL
        
        # Create Mail object
        mail = Mail(
            from_email=from_email,
            to_emails=recipient_list,
            subject=subject,
            plain_text_content=message
        )
        
        # Add HTML content if provided
        if html_message:
            mail.add_content(html_message, "text/html")
        
        # Send email
        response = sg.send(mail)
        
        if response.status_code in [200, 201, 202]:
            logger.info(f"Email sent successfully via SendGrid: {subject} to {recipient_list}")
            return True
        else:
            logger.error(f"SendGrid API error: {response.status_code} - {response.body}")
            return False
            
    except ImportError:
        logger.error("SendGrid library not installed. Install with: pip install sendgrid")
        return False
    except Exception as e:
        logger.error(f"SendGrid email sending failed: {str(e)}")
        return False

def get_sendgrid_status():
    """Get SendGrid configuration status"""
    if not is_sendgrid_configured():
        return "not_configured"
    
    try:
        import sendgrid
        return "configured"
    except ImportError:
        return "library_not_installed"
