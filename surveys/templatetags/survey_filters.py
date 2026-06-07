from django import template
import json

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


class _QuestionMeta:
    """Lightweight wrapper so templates can dot-access conditional config."""

    def __init__(self, data):
        self.key = data.get("key", "")
        self.part = data.get("part", "") or ""
        self.show_when = data.get("show_when", {}) or {}
        try:
            self.show_when_json = json.dumps(self.show_when)
        except (TypeError, ValueError):
            self.show_when_json = "{}"


@register.filter(name="load_question_meta")
def load_question_meta(help_text):
    """Parse JSON metadata stored in SurveyQuestion.help_text.

    Returns a ``_QuestionMeta`` object with safe defaults. If the help_text
    is empty or not valid JSON, returns an object with empty show_when.
    """
    if not help_text:
        return _QuestionMeta({})
    try:
        data = json.loads(help_text)
        if not isinstance(data, dict):
            return _QuestionMeta({})
        return _QuestionMeta(data)
    except (ValueError, TypeError):
        return _QuestionMeta({})