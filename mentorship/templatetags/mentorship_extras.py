from django import template
import logging

register = template.Library()
logger = logging.getLogger('mentorship')

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

@register.filter(name='safe_avatar')
def safe_avatar(user):
    """Safely get user avatar or return default"""
    try:
        if user and hasattr(user, 'profile') and user.profile and user.profile.avatar:
            return user.profile.avatar.url
        return '/static/images/default-avatar.png'
    except Exception as e:
        logger.warning(f"Error accessing avatar for user {getattr(user, 'id', 'unknown')}: {str(e)}")
        return '/static/images/default-avatar.png'

@register.filter(name='safe_location')
def safe_location(user):
    """Safely get user location or return default"""
    try:
        if user and hasattr(user, 'profile') and user.profile:
            # Try the location property first
            if hasattr(user.profile, 'location') and user.profile.location:
                return user.profile.location
            
            # Fallback to individual fields
            parts = []
            if hasattr(user.profile, 'city') and user.profile.city:
                parts.append(user.profile.city)
            if hasattr(user.profile, 'state') and user.profile.state:
                parts.append(user.profile.state)
            if hasattr(user.profile, 'country') and user.profile.country:
                parts.append(str(user.profile.country.name))
            
            if parts:
                return ", ".join(parts)
        
        return "Location not set"
    except Exception as e:
        logger.warning(f"Error accessing location for user {getattr(user, 'id', 'unknown')}: {str(e)}")
        return "Location not set"

@register.filter(name='safe_position')
def safe_position(user):
    """Safely get user current position or return empty string"""
    try:
        if user and hasattr(user, 'profile') and user.profile:
            if hasattr(user.profile, 'current_position') and user.profile.current_position:
                return user.profile.current_position
            # Also check for 'position' field as a fallback
            if hasattr(user.profile, 'position') and user.profile.position:
                return user.profile.position
        return ""
    except Exception as e:
        logger.warning(f"Error accessing position for user {getattr(user, 'id', 'unknown')}: {str(e)}")
        return ""
