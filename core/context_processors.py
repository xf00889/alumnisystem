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


def cms_contact_info(request):
    """
    Add CMS contact information to template context
    """
    try:
        from cms.models import ContactInfo
        contact_info = ContactInfo.objects.filter(is_active=True).order_by('contact_type', 'order')
        return {
            'cms_contact_info': contact_info,
        }
    except (ImportError, Exception):
        return {
            'cms_contact_info': [],
        }