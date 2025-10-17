"""
Context processors for the core app
"""
from .recaptcha_utils import get_recaptcha_public_key, is_recaptcha_enabled


def recaptcha_context(request):
    """
    Add reCAPTCHA configuration to template context
    """
    return {
        'recaptcha_public_key': get_recaptcha_public_key(),
        'recaptcha_enabled': is_recaptcha_enabled(),
    }