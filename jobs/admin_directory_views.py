"""Independent staff job views; never render alumni AI matching/application UI."""
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from .models import JobPosting
from .views import is_hr_or_admin


@login_required
def admin_job_board(request):
    if not is_hr_or_admin(request.user):
        raise PermissionDenied("Career administration requires HR or staff permission.")
    jobs = JobPosting.objects.exclude(slug='').select_related('posted_by')
    query = (request.GET.get('q') or '').strip()[:120]
    if query:
        jobs = jobs.filter(Q(job_title__icontains=query) | Q(company_name__icontains=query) | Q(location__icontains=query))
    state = request.GET.get('state', '')
    if state == 'active':
        jobs = jobs.filter(is_active=True)
    elif state == 'inactive':
        jobs = jobs.filter(is_active=False)
    source = request.GET.get('source_type', '')
    if source in dict(JobPosting.SOURCE_TYPE_CHOICES):
        jobs = jobs.filter(source_type=source)
    params = request.GET.copy()
    params.pop('page', None)
    return render(request, 'jobs/admin/job_board.html', {
        'jobs': Paginator(jobs.order_by('-posted_date', '-pk'), 20).get_page(request.GET.get('page')),
        'query': query,
        'current_state': state,
        'current_source': source,
        'source_types': JobPosting.SOURCE_TYPE_CHOICES,
        'filters_query': params.urlencode(),
    })


@login_required
def admin_job_details(request, slug):
    if not is_hr_or_admin(request.user):
        raise PermissionDenied("Career administration requires HR or staff permission.")
    job = get_object_or_404(JobPosting.objects.select_related('posted_by'), slug=slug)
    return render(request, 'jobs/admin/job_details.html', {
        'job': job,
        'applications_count': job.applications.count(),
    })
