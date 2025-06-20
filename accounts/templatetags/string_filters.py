from django import template

register = template.Library()

@register.filter
def split(value, delimiter=','):
    """
    Split a string by delimiter and return a list.
    Usage: {{ value|split:"," }}
    """
    if value:
        return value.split(delimiter)
    return []

@register.filter
def strip(value):
    """
    Strip whitespace from a string.
    Usage: {{ value|strip }}
    """
    if value:
        return value.strip()
    return ""

@register.filter
def callable(value):
    """
    Check if a value is callable.
    Usage: {{ value|callable }}
    """
    return hasattr(value, '__call__') 