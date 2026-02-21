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


@register.filter(name='format_acronym')
def format_acronym(text):
    """
    Format acronym text with large blue letters followed by descriptions.
    
    Expected format:
    A
    Achieve global recognition by program excellence
    
    S
    Strengthen research through impactful innovation
    
    Returns HTML with styled acronym letters and descriptions.
    """
    if not text:
        return ''
    
    # Split by newlines to get each line
    lines = text.strip().split('\n')
    
    html_parts = []
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Check if this is a single letter (acronym letter)
        if line and len(line) == 1 and line.isalpha():
            letter = line.upper()
            description = ''
            
            # Get the description (next non-empty line)
            i += 1
            if i < len(lines):
                description = lines[i].strip()
            
            # Create HTML for this acronym entry
            html_parts.append(
                f'<div class="acronym-entry">'
                f'<span class="acronym-letter">{letter}</span>'
                f'<span class="acronym-description">{description}</span>'
                f'</div>'
            )
        
        i += 1
    
    return mark_safe(''.join(html_parts))
