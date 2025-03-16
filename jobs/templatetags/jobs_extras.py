from django import template
import os

register = template.Library()

@register.filter
def filename(value):
    """Returns the filename from a file path."""
    return os.path.basename(str(value))

@register.filter
def is_hr_or_admin(user):
    """Check if user is HR or admin"""
    if user.is_superuser:
        return True
    return user.groups.filter(name='HR').exists()

@register.filter
def get_item(dictionary, key):
    """Gets an item from a dictionary by key."""
    return dictionary.get(key)

@register.filter
def status_color(status):
    """Maps job application status to a Bootstrap color class."""
    status_colors = {
        'PENDING': 'secondary',
        'REVIEWING': 'info',
        'SHORTLISTED': 'primary',
        'INTERVIEWED': 'warning',
        'ACCEPTED': 'success',
        'REJECTED': 'danger'
    }
    return status_colors.get(status, 'secondary') 