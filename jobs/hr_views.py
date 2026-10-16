"""Small, strictly career-scoped analytics dashboard for HR operators."""
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
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
    six_months_ago = timezone.now() - timedelta(days=185)
    trend = list(applications.filter(application_date__gte=six_months_ago)
                 .annotate(month=TruncMonth('application_date'))
                 .values('month').annotate(total=Count('pk')).order_by('month'))
    monthly = {point['month'].strftime('%Y-%m'):point['total'] for point in trend}
    from calendar import month_name
    labels, counts = [], []
    for months_back in range(5, -1, -1):
        year = timezone.localdate().year
        month = timezone.localdate().month - months_back
        while month < 1:
            year -= 1
            month += 12
        labels.append(f'{month_name[month][:3]} {year}')
        counts.append(monthly.get(f'{year}-{month:02d}', 0))
    return render(request, 'jobs/hr/dashboard.html', {
        'trend_chart': {'labels': labels, 'values': counts},
        'jobs_chart': {'labels': ['Internal applications', 'External postings'], 'values': [internal.count(), jobs.exclude(accepts_internal_applications=True).count()]},
        'active_jobs': jobs.filter(is_active=True).count(),
        'internal_jobs': internal.count(),
        'submitted_applications': applications.count(),
        'pending_applications': applications.filter(status='PENDING').count(),
        'reviewed_applications': applications.exclude(status='PENDING').count(),
        'latest_jobs': jobs.order_by('-posted_date')[:6],
        'recent_applications': applications.select_related('job', 'applicant').order_by('-application_date')[:6],
        'application_trend': trend,
    })
