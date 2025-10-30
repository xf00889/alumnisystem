"""
Context processors for the core app
"""
from .recaptcha_utils import get_recaptcha_public_key, is_recaptcha_enabled
from .sri_utils import LEAFLET_SRI_HASHES


def recaptcha_context(request):
    """
    Add reCAPTCHA configuration to template context
    """
    return {
        'recaptcha_public_key': get_recaptcha_public_key(),
        'recaptcha_enabled': is_recaptcha_enabled(),
    }


def sri_hashes(request):
    """
    Make SRI hashes available in all templates
    """
    return {
        'leaflet_sri_hashes': LEAFLET_SRI_HASHES
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