from django import template

register = template.Library()

@register.filter(name='multiply')
def multiply(value, arg):
    """Multiplies the value by the argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter(name='safe_avatar_url')
def safe_avatar_url(avatar_field, default_url='/static/images/default-avatar.png'):
    """
    Safely returns the avatar URL or a default URL if no avatar is set.
    Usage: {{ user.profile.avatar|safe_avatar_url }}
    """
    try:
        if avatar_field and hasattr(avatar_field, 'url'):
            return avatar_field.url
    except (ValueError, AttributeError):
        pass
    return default_url 