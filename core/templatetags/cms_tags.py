from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def get_contact_info():
    """
    Get contact information from CMS
    """
    try:
        from cms.models import ContactInfo
        contact_info = ContactInfo.objects.filter(is_active=True).order_by('contact_type', 'order')
        return contact_info
    except (ImportError, Exception):
        return []


@register.simple_tag
def get_site_config():
    """
    Get site configuration from CMS
    """
    try:
        from cms.models import SiteConfig
        return SiteConfig.get_site_config()
    except (ImportError, Exception):
        # Return a default object with empty values
        from types import SimpleNamespace
        return SimpleNamespace(
            site_name='NORSU Alumni Network',
            contact_email='alumni@norsu.edu.ph',
            contact_phone='+63 35 422 6002',
            contact_address='Negros Oriental State University\nDumaguete City, Philippines',
            facebook_url='',
            twitter_url='',
            linkedin_url='',
            instagram_url='',
            youtube_url='',
        )
