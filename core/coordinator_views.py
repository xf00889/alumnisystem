"""Campus-scoped coordinator overview. Never aggregate alumni outside assigned campuses."""
from datetime import datetime, timedelta
from calendar import month_abbr

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils import timezone

from alumni_directory.models import Alumni
from accounts.models import Mentor
from alumni_groups.models import AlumniGroup
from donations.models import Campaign, Donation
from events.models import Event
from announcements.models import Announcement
from .models.coordinator_campus import CoordinatorCampus


def _last_six_months():
    today = datetime.now(timezone.get_current_timezone()).date()
    periods = []
    for months_back in range(5, -1, -1):
        year, month = today.year, today.month - months_back
        while month <= 0:
            year -= 1
            month += 12
        periods.append((year, month, f'{month_abbr[month]} {year}'))
    return periods


@login_required
def coordinator_dashboard(request):
    user = request.user
    profile = getattr(user, 'profile', None)
    if user.is_superuser or user.is_staff or not (profile and profile.is_alumni_coordinator):
        raise PermissionDenied('Coordinator access required.')

    assigned = list(CoordinatorCampus.objects.filter(user=user).values_list('campus', flat=True))
    alumni = Alumni.objects.filter(campus__in=assigned)
    campus_names = dict(Alumni.CAMPUS_CHOICES)
    by_campus = dict(alumni.values('campus').annotate(total=Count('pk')).values_list('campus', 'total'))

    college_names = {
        'CAS': 'CAS · Arts & Sciences', 'CBA': 'CBA · Business',
        'CAFF': 'CAFF · Agriculture', 'CCJE': 'CCJE · Criminal Justice',
        'CEA': 'CEA · Engineering', 'CIT': 'CIT · Industrial Tech',
        'COL': 'COL · Law', 'CNPAHS': 'CNPAHS · Health Sciences',
        'CTE': 'CTE · Education', 'CTHM': 'CTHM · Tourism',
    }
    college_rows = list(alumni.values('college').annotate(total=Count('pk')).order_by('-total', 'college'))
    top_colleges = college_rows[:8]
    college_labels = [college_names.get(row['college'], row['college'] or 'Unspecified') for row in top_colleges]
    college_values = [row['total'] for row in top_colleges]
    if len(college_rows) > 8:
        college_labels.append('Other colleges')
        college_values.append(sum(row['total'] for row in college_rows[8:]))

    batch_rows = list(alumni.values('graduation_year').annotate(total=Count('pk')).order_by('-graduation_year')[:10])
    status_names = dict(Alumni.EMPLOYMENT_STATUS_CHOICES)
    status_rows = list(alumni.values('employment_status').annotate(total=Count('pk')).order_by('-total', 'employment_status'))

    periods = _last_six_months()
    # Profile creation date is the registration metric, not graduation date.
    trend_rows = alumni.filter(created_at__gte=timezone.now() - timedelta(days=200)).annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(total=Count('pk')).order_by('month')
    trend_map = {row['month'].strftime('%Y-%m'): row['total'] for row in trend_rows if row['month']}

    # Retain network-wide indicators, labeled as such rather than campus-scoped.
    network_counts = [Announcement.objects.count(), Event.objects.count(), Campaign.objects.count(), AlumniGroup.objects.count()]
    return render(request, 'admin/coordinator/dashboard.html', {
        'assigned_campuses': [campus_names[c] for c in assigned if c in campus_names],
        'total_alumni': alumni.count(),
        'verified_alumni': alumni.filter(is_verified=True).count(),
        'groups_count': network_counts[3],
        'mentors_count': Mentor.objects.filter(is_active=True, user__alumni__campus__in=assigned).distinct().count(),
        'announcements_count': network_counts[0],
        'events_count': network_counts[1],
        'campaign_count': network_counts[2],
        'donation_count': Donation.objects.count(),
        'campus_chart': {
            'labels': [campus_names[c] for c in assigned if c in campus_names],
            'values': [by_campus.get(c, 0) for c in assigned if c in campus_names],
        },
        'activity_chart': {'labels': ['Announcements', 'Events', 'Campaigns', 'Groups'], 'values': network_counts},
        'college_chart': {'labels': college_labels, 'values': college_values},
        'batch_chart': {'labels': [str(row['graduation_year']) for row in batch_rows], 'values': [row['total'] for row in batch_rows]},
        'registration_chart': {'labels': [label for _, _, label in periods], 'values': [trend_map.get(f'{y}-{m:02d}', 0) for y, m, _ in periods]},
        'employment_chart': {
            'labels': [status_names.get(row['employment_status'], row['employment_status'] or 'Unspecified') for row in status_rows],
            'values': [row['total'] for row in status_rows],
        },
        'recent_alumni': alumni.select_related('user').order_by('-pk')[:6],
    })
