"""Staff-only directory employability snapshots using existing tracer answer semantics.

All rates are survey-respondent rates, not registry-wide employment rates.
The calendar period sets the snapshot date; dated current-job starts in that
period are a separate metric. No personal-level information is exported.
"""
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponseBadRequest
from django.views.decorators.http import require_GET

from alumni_directory.directory_search import normalize_directory_search, with_alumni_name_search
from alumni_directory.models import Alumni
from core.report_periods import export_download_name, parse_report_period
from surveys.employability_reports import (
    _aggregate, _answer_map, _export_report, _parse_job_start,
)
from surveys.models import SurveyResponse
from surveys.tracer_metadata import ALUMNI_TITLE
from surveys.tracer_study import _can_view_tracer_reports


SUPPORTED_PERIODS = ('monthly', 'quarterly', 'semi_annual', 'annual')


def _scoped_query_for_export(request):
    # Import the existing access policy rather than broadening coordinator access.
    from alumni_directory.views import coordinator_scoped_alumni

    queryset = coordinator_scoped_alumni(request, Alumni.objects.all())
    query = normalize_directory_search(request.GET.get('search', ''))
    if query:
        queryset, name_match = with_alumni_name_search(queryset, query)
        college_lookup = Q()
        for code, name in Alumni.COLLEGE_CHOICES:
            if query.casefold() in name.casefold():
                college_lookup |= Q(college=code)
        queryset = queryset.filter(
            name_match | Q(course__icontains=query) | Q(city__icontains=query) |
            Q(province__icontains=query) | Q(current_company__icontains=query) |
            Q(job_title__icontains=query) | college_lookup
        )
    for param, model_field in (
        ('graduation_year', 'graduation_year'), ('course', 'course'),
        ('college', 'college'), ('campus', 'campus'),
        ('province', 'province'), ('employment_status', 'employment_status'),
    ):
        values = [item for item in request.GET.getlist(param) if item]
        if values:
            queryset = queryset.filter(**{f'{model_field}__in': values})
    return queryset


def _values(params, name):
    values = params.getlist(name) if hasattr(params, 'getlist') else params.get(name, [])
    if isinstance(values, str):
        values = [values]
    return [value for value in values if value]


def _selected_year(params):
    raw = _values(params, 'graduation_year')
    if len(raw) != 1 or not raw[0].isdigit():
        raise ValueError('Select one graduation year to view the employability report.')
    cohort_year = int(raw[0])
    if cohort_year < 1900 or cohort_year > 2200:
        raise ValueError('Select a valid graduation year.')
    return cohort_year


def build_directory_employability(queryset, params, *, today=None):
    """Build a survey-response snapshot for the *already scoped* alumni queryset.

    Never infer a hire date from survey submission, nor count nonresponders as
    unemployed. Exports reuse the existing NORSU employability formatter.
    """
    cohort_year = _selected_year(params)
    today = today or datetime.now(ZoneInfo(settings.TIME_ZONE)).date()
    period_args = {
        'period': params.get('period') or 'annual',
        'year': params.get('year') or today.year,
        'month': params.get('month'),
        'quarter': params.get('quarter'),
        'half': params.get('half'),
    }
    period = parse_report_period(period_args, today=today)
    if period.kind not in SUPPORTED_PERIODS:
        raise ValueError('Choose monthly, quarterly, semi-annual, or annual.')
    if period.start > today:
        raise ValueError('The selected reporting period has not started yet.')
    as_of = min(period.end, today)
    cutoff = datetime.combine(as_of + timedelta(days=1), time.min)
    if settings.USE_TZ:
        from django.utils import timezone
        cutoff = timezone.make_aware(cutoff, timezone.get_default_timezone())

    eligible_total = queryset.count()
    responses = (
        SurveyResponse.objects.filter(
            survey__title=ALUMNI_TITLE, alumni__in=queryset,
            submitted_at__lt=cutoff,
        )
        .select_related('alumni')
        .prefetch_related('answers__question', 'answers__selected_option')
        .order_by('alumni_id', '-submitted_at', '-pk')
    )
    seen, cohort, starts, employed_ids, undated_ids = set(), [], [], set(), set()
    for response in responses:
        if response.alumni_id in seen:
            continue
        seen.add(response.alumni_id)
        answers = _answer_map(response)
        alumni = response.alumni
        cohort.append((alumni.pk, alumni.campus, alumni.college))
        if (answers.get('p3_employed') or '').strip().casefold() != 'yes':
            continue
        employed_ids.add(alumni.pk)
        raw_start = answers.get('p3_current_job_start')
        started = _parse_job_start(raw_start, as_of) if raw_start else None
        if started is None:
            undated_ids.add(alumni.pk)
        elif period.start <= started <= as_of:
            starts.append((alumni.pk, started))

    result = _aggregate(
        cohort, starts, dict(Alumni.CAMPUS_CHOICES), dict(Alumni.COLLEGE_CHOICES),
        employed_ids=employed_ids, undated_ids=undated_ids,
    )
    selected_colleges = _values(params, 'college')
    selected_courses = _values(params, 'course')
    scope_label = ', '.join(
        [f'Class {cohort_year}']
        + ([f'College: {", ".join(selected_colleges)}'] if selected_colleges else [])
        + ([f'Program: {", ".join(selected_courses)}'] if selected_courses else [])
    )
    result.update({
        'eligible_total': eligible_total,
        'cohort_year': cohort_year,
        'report_year': period.start.year,
        'as_of': as_of,
        'period': period,
        'period_kind': period.kind,
        'scope_label': scope_label,
        'employment_rate_display': f"{result['rate']:.2f}%" if result['graduates'] else 'N/A',
        'response_coverage': round(100 * result['graduates'] / eligible_total, 2) if eligible_total else 0,
        'methodology': (
            f'{scope_label}. Source: latest submitted NORSU alumni tracer response for each eligible alumnus '
            f'as of {as_of.isoformat()}. Employment rate is reported-employed / tracer respondents, '
            'NOT employed / all registered alumni. Reporting period sets the as-of snapshot; '
            'dated current-job starts are counted separately when their start dates fall inside '
            'the selected period. Unknown dates are not assigned to a period. Employment is self-reported. '
            'Current directory filters and coordinator campus access are applied.'
        ),
    })
    return result


@login_required
@require_GET
def directory_employability_export(request):
    if not _can_view_tracer_reports(request.user):
        raise Http404
    requested_format = (request.GET.get('format') or '').lower()
    if requested_format not in ('csv', 'xlsx', 'excel', 'pdf'):
        raise Http404('Unsupported export format')
    try:
        report = build_directory_employability(_scoped_query_for_export(request), request.GET)
    except ValueError as error:
        return HttpResponseBadRequest(str(error))
    if not report['graduates']:
        return HttpResponseBadRequest('There are no tracer responses for the selected filters and period.')
    response = _export_report(report, requested_format)
    # Distinct filenames for different academic subsets of the same cohort.
    extension = 'xlsx' if requested_format in ('excel', 'xlsx') else requested_format
    suffix = '_'.join(
        [f"class-{report['cohort_year']}"]
        + [f"college-{','.join(_values(request.GET, 'college'))}"]
        + [f"program-{','.join(_values(request.GET, 'course'))}"]
    )
    response['Content-Disposition'] = (
        f'attachment; filename="{export_download_name("directory_employability_" + suffix, report["period"], extension)}"'
    )
    return response
