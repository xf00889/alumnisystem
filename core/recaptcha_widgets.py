"""
Custom reCAPTCHA widgets that use database configuration
"""
from django_recaptcha.widgets import ReCaptchaV3
from .recaptcha_utils import get_recaptcha_public_key, is_recaptcha_enabled


class DatabaseReCaptchaV3(ReCaptchaV3):
    """
    Custom reCAPTCHA v3 widget that uses database configuration
    """
    
    def __init__(self, *args, **kwargs):
        # Get the public key from database configuration
        public_key = get_recaptcha_public_key()
        
        # Set the public key in the widget's attrs
        if 'attrs' not in kwargs:
            kwargs['attrs'] = {}
        
        # Add the public key to the widget attributes
        kwargs['attrs']['data-sitekey'] = public_key
        
        super().__init__(*args, **kwargs)
    
    def render(self, name, value, attrs=None, renderer=None):
        # Only render if reCAPTCHA is enabled and has a valid key
        if not is_recaptcha_enabled():
            return ''
        
        # Ensure the public key is always set from database
        if attrs is None:
            attrs = {}
        
        public_key = get_recaptcha_public_key()
        if not public_key:
            return ''
        
        attrs['data-sitekey'] = public_key
        
        return super().render(name, value, attrs, renderer)
    
    def value_from_datadict(self, data, files, name):
        # Only process reCAPTCHA value if enabled
        if not is_recaptcha_enabled():
            return None
        
        return super().value_from_datadict(data, files, name)
