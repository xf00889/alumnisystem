from django import template

register = template.Library()

@register.filter
def campus_short_name(campus_display):
    """
    Convert full campus name to abbreviated format for display.
    Example: "Dumaguete Main Campus" -> "Main"
    """
    if not campus_display:
        return "Not specified"
    
    # Mapping of campus names to abbreviations
    campus_map = {
        'Dumaguete Main Campus': 'Main',
        'Bais City Campus I': 'Bais I',
        'Bais City Campus II': 'Bais II',
        'Bayawan-Sta. Catalina Campus': 'BSC',
        'Siaton Campus': 'Siaton',
        'Guihulngan Campus': 'Guihulngan',
        'Pamplona Campus': 'Pamplona',
        'Mabinay Campus': 'Mabinay',
    }
    
    return campus_map.get(campus_display, campus_display)
