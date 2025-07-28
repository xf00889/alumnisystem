from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
import json

register = template.Library()

@register.filter
@stringfilter
def parse_json_list(value):
    """
    Parse a JSON string into a list. If parsing fails, return an empty list.
    Usage: {{ completed_items|parse_json_list }}
    """
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return []

@register.filter
def get_progress_percentage(completed_items):
    """
    Calculate the percentage of completed items.
    Usage: {{ completed_items|get_progress_percentage }}
    """
    try:
        items = json.loads(completed_items) if isinstance(completed_items, str) else completed_items
        if not items:
            return 0
        completed = sum(1 for item in items if item.get('status') == 'completed')
        return int((completed / len(items)) * 100)
    except (ValueError, TypeError, AttributeError):
        return 0

@register.filter
def format_duration(minutes):
    """
    Format duration in minutes to a human-readable string.
    Usage: {{ meeting.duration|format_duration }}
    """
    if not isinstance(minutes, (int, float)):
        return "N/A"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if hours > 0 and remaining_minutes > 0:
        return f"{hours}h {remaining_minutes}m"
    elif hours > 0:
        return f"{hours}h"
    else:
        return f"{remaining_minutes}m"

@register.filter
def status_badge(status):
    """
    Convert a status string into a Bootstrap badge with appropriate color.
    Usage: {{ meeting.status|status_badge|safe }}
    """
    status = status.upper()
    badge_classes = {
        'SCHEDULED': 'bg-primary',
        'COMPLETED': 'bg-success',
        'CANCELLED': 'bg-danger',
        'RESCHEDULED': 'bg-warning',
        'PENDING': 'bg-info',
        'IN_PROGRESS': 'bg-info',
        'NOT_STARTED': 'bg-secondary',
        'DEFERRED': 'bg-warning',
    }
    badge_class = badge_classes.get(status, 'bg-secondary')
    return mark_safe(f'<span class="badge {badge_class}">{status.title()}</span>')

@register.filter
def multiply(value, arg):
    """
    Multiply the value by the argument.
    Usage: {{ value|multiply:2 }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
@stringfilter
def basename(value):
    """
    Extract the filename from a file path.
    Usage: {{ file_path|basename }}
    """
    import os
    return os.path.basename(value)