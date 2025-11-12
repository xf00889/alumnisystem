from django import template

register = template.Library()

@register.filter(name='multiply')
def multiply(value, arg):
    """
    Multiply the value by the argument.
    Usage: {{ value|multiply:2 }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter(name='replace')
def replace(value, arg):
    """
    Replace characters in a string.
    Usage: {{ value|replace:"_:" }} replaces underscore with space (default)
    Usage: {{ value|replace:"_:-" }} replaces underscore with dash
    Format: "old:new" where old is the character to replace and new is the replacement
    If new is empty (just "old:"), replaces with space by default
    """
    try:
        if ':' in arg:
            parts = arg.split(':', 1)
            old = parts[0]
            new = parts[1] if len(parts) > 1 and parts[1] else ' '
            return str(value).replace(old, new)
        else:
            # If no colon, just replace with space (default behavior)
            return str(value).replace(arg, ' ')
    except (ValueError, TypeError, AttributeError):
        return value 