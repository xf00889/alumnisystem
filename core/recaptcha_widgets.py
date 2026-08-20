"""
Custom reCAPTCHA widgets that use database configuration
"""
from django_recaptcha.widgets import ReCaptchaV3
from .recaptcha_utils import get_recaptcha_public_key, is_recaptcha_enabled


class DatabaseReCaptchaV3(ReCaptchaV3):
    """
    Custom reCAPTCHA v3 widget that uses database configuration
    """
    template_name = 'core/widgets/lazy_recaptcha_v3.html'
    
    def __init__(self, *args, **kwargs):
        # Get the public key from database configuration
        public_key = get_recaptcha_public_key()
        
        # Set the public key in the widget's attrs
        if 'attrs' not in kwargs:
            kwargs['attrs'] = {}
        
        # Add the public key to the widget attributes
        kwargs['attrs']['data-sitekey'] = public_key
        
        super().__init__(*args, **kwargs)

        # The upstream g-recaptcha class triggers an additional visible widget
        # when Google's API scans the page. Use a dedicated hook for the lazy
        # v3 controller so only one invisible verification flow is created.
        classes = self.attrs.get('class', '').split()
        classes = [name for name in classes if name != 'g-recaptcha']
        if 'norsu-recaptcha-v3' not in classes:
            classes.append('norsu-recaptcha-v3')
        self.attrs['class'] = ' '.join(classes)

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs.pop('data-size', None)
        return attrs
    
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
