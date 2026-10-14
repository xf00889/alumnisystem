"""Shared, validated calendar windows and deterministic report download names.

All periods are inclusive *calendar dates* in the application's local time zone.
A missing period preserves existing all-time exports. Date ranges only apply to
records with a documented date field; this module never guesses one.
"""
import calendar
from dataclasses import dataclass
from datetime import date, timedelta
import re


@dataclass(frozen=True)
class ReportPeriod:
    start: date | None
    end: date | None
    slug: str
    label: str
    kind: str = 'all'

    def filter_queryset(self, queryset, date_field):
        if self.start is None and self.end is None:
            return queryset
        field = queryset.model._meta.get_field(date_field)
        is_date = field.get_internal_type() == 'DateField'
        suffix = '' if is_date else '__date'
        filters = {}
        if self.start is not None:
            filters[f'{date_field}{suffix}__gte'] = self.start
        if self.end is not None:
            filters[f'{date_field}{suffix}__lte'] = self.end
        return queryset.filter(**filters)


def _parse_date(raw):
    try:
        return date.fromisoformat(raw or '')
    except (TypeError, ValueError):
        raise ValueError('Enter a valid date in YYYY-MM-DD format.') from None


def _number(raw, label, minimum, maximum):
    try:
        number = int(raw)
    except (TypeError, ValueError):
        raise ValueError(f'Select a valid {label}.') from None
    if not minimum <= number <= maximum:
        raise ValueError(f'Select a valid {label}.')
    return number


def parse_report_period(params, *, today=None):
    today = today or date.today()
    mode = (params.get('period') or '').strip().lower().replace('-', '_')
    if not mode:
        # Existing date-range links should continue to work, with explicit naming.
        mode = 'custom' if (params.get('start_date') or params.get('end_date')) else 'all'
    if mode in ('all', 'all_time'):
        return ReportPeriod(None, None, 'all-time', 'All dates')
    if mode in ('day', 'one_day', 'single_day'):
        target = _parse_date(params.get('day') or params.get('start_date'))
        return ReportPeriod(target, target, f'one-day_{target.isoformat()}', target.isoformat(), 'day')
    if mode == 'custom':
        start, end = _parse_date(params.get('start_date')), _parse_date(params.get('end_date'))
        if start > end:
            raise ValueError('The start date must be on or before the end date.')
        if start == end:
            return ReportPeriod(start, end, f'one-day_{start.isoformat()}', start.isoformat(), 'day')
        return ReportPeriod(start, end, f'custom_{start.isoformat()}_to_{end.isoformat()}', f'{start} to {end}', 'custom')
    if mode not in ('monthly', 'quarterly', 'semi_annual', 'annual'):
        raise ValueError('Select a supported report period.')
    year = _number(params.get('year') or today.year, 'year', 1900, 2200)
    if mode == 'monthly':
        month = _number(params.get('month') or today.month, 'month', 1, 12)
        start = date(year, month, 1)
        end = date(year, month, calendar.monthrange(year, month)[1])
        return ReportPeriod(start, end, f'monthly_{year}-{month:02d}', start.strftime('%B %Y'), mode)
    if mode == 'quarterly':
        quarter = _number(params.get('quarter') or (today.month - 1) // 3 + 1, 'quarter', 1, 4)
        first, last = (quarter - 1) * 3 + 1, quarter * 3
        start, end = date(year, first, 1), date(year, last, calendar.monthrange(year, last)[1])
        return ReportPeriod(start, end, f'quarterly_{year}-Q{quarter}', f'Q{quarter} {year}', mode)
    if mode == 'semi_annual':
        half = _number(params.get('half') or (1 if today.month <= 6 else 2), 'half-year', 1, 2)
        start, end = date(year, 1 if half == 1 else 7, 1), date(year, 6 if half == 1 else 12, 30 if half == 1 else 31)
        return ReportPeriod(start, end, f'semi-annual_{year}-H{half}', f'H{half} {year}', mode)
    return ReportPeriod(date(year, 1, 1), date(year, 12, 31), f'annual_{year}', str(year), mode)


def export_download_name(subject, period, extension):
    safe_subject = re.sub(r'[^a-z0-9_-]+', '-', str(subject).lower()).strip('-_') or 'report'
    if not re.fullmatch(r'[a-z0-9]{2,6}', extension):
        raise ValueError('Unsupported file extension.')
    return f'norsu_{safe_subject}_{period.slug}.{extension}'


def legacy_date_window(start, end):
    """Describe optional pre-existing from/to filters without changing their scope."""
    if start and end:
        return parse_report_period({'period': 'custom', 'start_date': start, 'end_date': end})
    if start:
        first = _parse_date(start)
        return ReportPeriod(first, None, f'from_{first.isoformat()}', f'From {first}', 'from')
    if end:
        last = _parse_date(end)
        return ReportPeriod(None, last, f'through_{last.isoformat()}', f'Through {last}', 'through')
    return ReportPeriod(None, None, 'all-time', 'All dates')
