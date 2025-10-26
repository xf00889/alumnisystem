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
