"""Career-scoped HR reporting (portal applications only)."""
from calendar import month_abbr
from datetime import datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils import timezone

from .hr_access import is_hr_only
from .models import JobApplication, JobPosting


@login_required
def hr_dashboard(request):
    if not is_hr_only(request.user):
        raise PermissionDenied('This workspace is for HR accounts.')

    jobs = JobPosting.objects.exclude(slug='')
    internal = jobs.filter(accepts_internal_applications=True)
    applications = JobApplication.objects.filter(job__accepts_internal_applications=True)
    trend = list(applications.filter(application_date__gte=timezone.now() - timedelta(days=200))
                 .annotate(month=TruncMonth('application_date'))
                 .values('month').annotate(total=Count('pk')).order_by('month'))
    monthly = {point['month'].strftime('%Y-%m'): point['total'] for point in trend if point['month']}
    today = datetime.now(timezone.get_current_timezone()).date()
    labels, counts = [], []
    for months_back in range(5, -1, -1):
        year, month = today.year, today.month - months_back
        while month < 1:
            year -= 1
            month += 12
        labels.append(f'{month_abbr[month]} {year}')
        counts.append(monthly.get(f'{year}-{month:02d}', 0))

    status_count = dict(applications.values('status').annotate(total=Count('pk')).values_list('status', 'total'))
    job_types = dict(jobs.filter(is_active=True).values('job_type').annotate(total=Count('pk')).values_list('job_type', 'total'))
    top_roles = list(applications.values('job_id', 'job__job_title').annotate(total=Count('pk')).order_by('-total', 'job__job_title', 'job_id')[:8])

    return render(request, 'jobs/hr/dashboard.html', {
        'trend_chart': {'labels': labels, 'values': counts},
        'jobs_chart': {'labels': ['Portal applications enabled', 'External-only postings'],
                       'values': [internal.count(), jobs.exclude(accepts_internal_applications=True).count()]},
        'status_chart': {'labels': [label for _, label in JobApplication.STATUS_CHOICES],
                         'values': [status_count.get(code, 0) for code, _ in JobApplication.STATUS_CHOICES]},
        'positions_chart': {'labels': [row['job__job_title'] for row in top_roles],
                            'values': [row['total'] for row in top_roles]},
        'types_chart': {'labels': [label for _, label in JobPosting.JOB_TYPE_CHOICES],
                        'values': [job_types.get(code, 0) for code, _ in JobPosting.JOB_TYPE_CHOICES]},
        'active_jobs': jobs.filter(is_active=True).count(),
        'internal_jobs': internal.count(),
        'submitted_applications': applications.count(),
        'pending_applications': status_count.get('PENDING', 0),
        'reviewed_applications': applications.exclude(status='PENDING').count(),
        'latest_jobs': jobs.order_by('-posted_date')[:6],
        'recent_applications': applications.select_related('job', 'applicant').order_by('-application_date')[:6],
        'application_trend': trend,
    })
