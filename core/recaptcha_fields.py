"""
Custom reCAPTCHA fields that use database configuration
"""
from django_recaptcha.fields import ReCaptchaField
from .recaptcha_utils import is_recaptcha_enabled, get_recaptcha_config
from django.core.exceptions import ValidationError


class DatabaseReCaptchaField(ReCaptchaField):
    """
    Custom reCAPTCHA field that uses database configuration
    """
    
    def __init__(self, *args, **kwargs):
        # Only initialize if reCAPTCHA is enabled
        if not is_recaptcha_enabled():
            # If reCAPTCHA is not enabled, make this field optional and skip validation
            kwargs['required'] = False
            super().__init__(*args, **kwargs)
            return
        
        # Get the database configuration
        config = get_recaptcha_config()
        if not config:
            # If no configuration, make field optional
            kwargs['required'] = False
            super().__init__(*args, **kwargs)
            return
        
        # Initialize with database configuration
        super().__init__(*args, **kwargs)
    
    def validate(self, value):
        """
        Custom validation that uses database configuration
        """
        # If reCAPTCHA is not enabled, skip validation
        if not is_recaptcha_enabled():
            return
        
        # Get the database configuration
        config = get_recaptcha_config()
        if not config:
            # If no configuration, skip validation
            return
        
        # If no value provided, skip validation (field is optional)
        if not value:
            return
        
        # If value is provided, verify it using database configuration
        try:
            result = config.verify_token(value)
            if not result.get('success', False):
                error_codes = result.get('error_codes', [])
                if error_codes:
                    raise ValidationError(f'reCAPTCHA verification failed: {", ".join(error_codes)}')
                else:
                    raise ValidationError('reCAPTCHA verification failed. Please try again.')
        except Exception as e:
            # Log the error but don't block login
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'reCAPTCHA verification error: {e}')
            # Allow login to proceed if verification fails
            return
    
    def clean(self, value):
        """
        Clean method that handles database configuration
        """
        # If reCAPTCHA is not enabled, return None
        if not is_recaptcha_enabled():
            return None
        
        # Get the database configuration
        config = get_recaptcha_config()
        if not config:
            return None
        
        # If no value and not required, return None
        if not value and not self.required:
            return None
        
        # Validate the value
        self.validate(value)
        return value
