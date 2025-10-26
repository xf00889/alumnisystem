from django import template

register = template.Library()

@register.inclusion_tag('partials/footer_contact.html')
def footer_contact_info():
    """
    Inclusion tag to render contact information in the footer
    """
    try:
        from cms.models import ContactInfo
        contact_info = ContactInfo.objects.filter(is_active=True).order_by('contact_type', 'order')
        return {'contact_info': contact_info}
    except (ImportError, Exception):
        return {'contact_info': []}

