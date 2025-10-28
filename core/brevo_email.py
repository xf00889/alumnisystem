"""
Brevo Email Utilities
"""
import requests
import logging
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

def get_brevo_settings():
    """
    Get Brevo settings from database or fallback to Django settings
    """
    try:
        # Try to get from cache first
        brevo_settings = cache.get('brevo_settings')
        
        if brevo_settings is None:
            # Import here to avoid circular imports
            from .models.brevo_config import BrevoConfig
            
            # Get active Brevo configuration
            active_config = BrevoConfig.objects.filter(is_active=True, is_verified=True).first()
            
            if active_config:
                brevo_settings = active_config.get_connection_params()
                # Cache for 1 hour
                cache.set('brevo_settings', brevo_settings, 3600)
                logger.info(f"Loaded Brevo settings from database: {active_config.name}")
            else:
                # Fallback to Django settings
                from django.conf import settings
                brevo_settings = {
                    'api_key': getattr(settings, 'BREVO_API_KEY', ''),
                    'api_url': getattr(settings, 'BREVO_API_URL', 'https://api.brevo.com/v3/smtp/email'),
                    'from_email': getattr(settings, 'BREVO_FROM_EMAIL', 'noreply@example.com'),
                    'from_name': getattr(settings, 'BREVO_FROM_NAME', 'NORSU Alumni System'),
                }
                logger.warning("No active Brevo configuration found, using Django settings")
        
        return brevo_settings
        
    except Exception as e:
        logger.error(f"Error loading Brevo settings: {str(e)}")
        # Return default settings
        return {
            'api_key': '',
            'api_url': 'https://api.brevo.com/v3/smtp/email',
            'from_email': 'noreply@example.com',
            'from_name': 'NORSU Alumni System',
        }

def send_email_with_brevo(subject, message, recipient_list, from_email=None, from_name=None, html_message=None, fail_silently=False):
    """
    Send email using Brevo API
    
    Args:
        subject: Email subject
        message: Plain text message
        recipient_list: List of recipient email addresses
        from_email: Sender email address (optional)
        from_name: Sender name (optional)
        html_message: HTML version of the message (optional)
        fail_silently: Whether to fail silently on errors
    """
    try:
        brevo_settings = get_brevo_settings()
        
        # Validate API key
        if not brevo_settings.get('api_key'):
            raise ImproperlyConfigured("Brevo API key is not configured")
        
        # Use provided from_email or fallback to settings
        if from_email is None:
            from_email = brevo_settings.get('from_email')
        
        if from_name is None:
            from_name = brevo_settings.get('from_name', 'NORSU Alumni System')
        
        # Prepare headers
        headers = {
            'accept': 'application/json',
            'api-key': brevo_settings['api_key'],
            'content-type': 'application/json'
        }
        
        # Prepare email data
        email_data = {
            "sender": {
                "name": from_name,
                "email": from_email
            },
            "to": [
                {
                    "email": email,
                    "name": email.split('@')[0]  # Use email prefix as name
                } for email in recipient_list
            ],
            "subject": subject,
            "textContent": message
        }
        
        # Add HTML content if provided
        if html_message:
            email_data["htmlContent"] = html_message
        
        # Send email via Brevo API
        response = requests.post(
            brevo_settings['api_url'],
            headers=headers,
            json=email_data,
            timeout=30
        )
        
        if response.status_code == 201:
            logger.info(f"Email sent successfully via Brevo to {recipient_list}")
            return True
        else:
            error_msg = f"Brevo API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            if not fail_silently:
                raise Exception(error_msg)
            return False
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Brevo API request failed: {str(e)}"
        logger.error(error_msg)
        if not fail_silently:
            raise Exception(error_msg)
        return False
        
    except Exception as e:
        error_msg = f"Failed to send email via Brevo: {str(e)}"
        logger.error(error_msg)
        if not fail_silently:
            raise
        return False

def test_brevo_connection():
    """
    Test Brevo API connection using current settings
    """
    try:
        brevo_settings = get_brevo_settings()
        
        if not brevo_settings.get('api_key'):
            return False, "Brevo API key is not configured"
        
        # Test API key validity by making a simple request
        headers = {
            'accept': 'application/json',
            'api-key': brevo_settings['api_key'],
            'content-type': 'application/json'
        }
        
        # Use the account info endpoint for testing
        account_url = "https://api.brevo.com/v3/account"
        response = requests.get(account_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return True, "Brevo API connection successful"
        else:
            return False, f"Brevo API error: {response.status_code} - {response.text}"
            
    except requests.exceptions.RequestException as e:
        return False, f"Brevo API request failed: {str(e)}"
    except Exception as e:
        return False, f"Brevo connection test failed: {str(e)}"

def clear_brevo_cache():
    """
    Clear Brevo settings cache
    """
    cache.delete('brevo_settings')
    logger.info("Brevo settings cache cleared")

def get_current_brevo_info():
    """
    Get information about the current Brevo configuration being used
    """
    try:
        brevo_settings = get_brevo_settings()
        return {
            'provider': 'Brevo',
            'api_url': brevo_settings.get('api_url', 'Not configured'),
            'from_email': brevo_settings.get('from_email', 'Not configured'),
            'from_name': brevo_settings.get('from_name', 'Not configured'),
            'api_key_configured': bool(brevo_settings.get('api_key')),
        }
    except Exception as e:
        logger.error(f"Error getting Brevo info: {str(e)}")
        return {
            'provider': 'Brevo',
            'error': str(e)
        }
