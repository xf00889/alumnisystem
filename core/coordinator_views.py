"""Alumni Coordinator workspace: relevant campus analytics only."""
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone
from alumni_directory.models import Alumni
from accounts.models import Mentor
from alumni_groups.models import AlumniGroup
from donations.models import Campaign, Donation
from events.models import Event
from announcements.models import Announcement
from .models.coordinator_campus import CoordinatorCampus

@login_required
def coordinator_dashboard(request):
    user = request.user
    profile = getattr(user, 'profile', None)
    if user.is_superuser or user.is_staff or not (profile and profile.is_alumni_coordinator):
        raise PermissionDenied('Coordinator access required.')
    assigned = list(CoordinatorCampus.objects.filter(user=user).values_list('campus',flat=True))
    alumni = Alumni.objects.filter(campus__in=assigned)
    by_campus = dict(alumni.values('campus').annotate(total=Count('pk')).values_list('campus','total'))
    campus_names = dict(Alumni.CAMPUS_CHOICES)
    return render(request,'admin/coordinator/dashboard.html',{
        'assigned_campuses': [campus_names[c] for c in assigned if c in campus_names],
        'total_alumni': alumni.count(),
        'verified_alumni': alumni.filter(is_verified=True).count(),
        'groups_count': AlumniGroup.objects.count(),
        'mentors_count': Mentor.objects.filter(is_active=True, user__alumni__campus__in=assigned).distinct().count(),
        'announcements_count': Announcement.objects.count(),
        'events_count': Event.objects.count(),
        'campaign_count': Campaign.objects.count(),
        'donation_count': Donation.objects.count(),
        'campus_chart': {'labels':[campus_names[c] for c in assigned if c in campus_names], 'values':[by_campus.get(c,0) for c in assigned if c in campus_names]},
        'activity_chart': {'labels':['Announcements','Events','Campaigns','Groups'], 'values':[Announcement.objects.count(), Event.objects.count(), Campaign.objects.count(), AlumniGroup.objects.count()]},
        'recent_alumni': alumni.select_related('user').order_by('-pk')[:6],
    })
