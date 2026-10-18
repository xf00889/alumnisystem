"""Calendar-day helper for visitor analytics under both Django timezone modes.

The project currently uses USE_TZ=False. Django's timezone.localdate() always
converts via localtime() and raises ValueError when given a naive datetime.
Use this helper in views, request sampling, and retention so their calendar
days agree, without changing the global timezone policy.
"""
from datetime import datetime

from django.utils import timezone


def visitor_local_date(value=None):
    """Return the active Django time zone's calendar date.

    If given a naive datetime (Django with USE_TZ=False), interpret its date
    as local wall-clock time rather than trying to call timezone.localtime().
    """
    if value is None:
        # Explicit time zone makes the day's boundary independent of VPS OS TZ.
        return datetime.now(timezone.get_current_timezone()).date()
    if timezone.is_aware(value):
        return timezone.localtime(value).date()
    return value.date()
