from django import template

register = template.Library()

@register.filter(name='multiply')
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0 

@register.filter(name='filter_by_mentee')
def filter_by_mentee(meetings, mentee):
    """Filter a list of meetings by mentee"""
    if not meetings or not mentee:
        return []
    
    return [meeting for meeting in meetings if meeting.mentorship.mentee.id == mentee.id] 

@register.filter(name='first_letters')
def first_letters(value):
    """Extract the first letter of each word in a string"""
    if not value:
        return ""

    words = value.split()
    if not words:
        return ""

    # Get first letter of each word, up to 2 letters
    initials = [word[0].upper() for word in words if word]
    return ''.join(initials[:2])

@register.filter(name='format_location')
def format_location(profile):
    """Format user location from profile with proper fallbacks"""
    if not profile:
        return "Location not set"

    # Try the location property first
    if hasattr(profile, 'location') and profile.location:
        return profile.location

    # Fallback to individual fields
    parts = []
    if hasattr(profile, 'city') and profile.city:
        parts.append(profile.city)
    if hasattr(profile, 'state') and profile.state:
        parts.append(profile.state)
    if hasattr(profile, 'country') and profile.country:
        parts.append(str(profile.country.name))

    return ", ".join(parts) if parts else "Location not set"