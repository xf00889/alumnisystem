from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import JsonResponse

# Import models from different apps
from accounts.models import User
from donations.models import Donation, Campaign
from events.models import Event, EventRSVP
from jobs.models import JobPosting, JobApplication
from accounts.models import MentorshipRequest, Mentor
from surveys.models import Survey, SurveyResponse
from announcements.models import Announcement
from feedback.models import Feedback
from alumni_directory.models import Alumni

@login_required
def admin_dashboard(request):
    """Main admin dashboard with comprehensive analytics"""
    # Check if user is staff or admin
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('core:home')
    
    # Get current date and calculate date ranges
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)
    
    # User Statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(last_login__gte=thirty_days_ago).count()
    new_users_this_month = User.objects.filter(date_joined__gte=thirty_days_ago).count()
    
    # Alumni Statistics
    total_alumni = Alumni.objects.count()
    verified_alumni = Alumni.objects.filter(is_verified=True).count()
    
    # Donation Statistics
    total_donations = Donation.objects.filter(status='completed').aggregate(
        total=Sum('amount')
    )['total'] or 0
    donation_count = Donation.objects.filter(status='completed').count()
    active_campaigns = Campaign.objects.filter(status='active').count()
    
    # Event Statistics
    total_events = Event.objects.count()
    upcoming_events = Event.objects.filter(start_date__gte=now).count()
    total_rsvps = EventRSVP.objects.count()
    
    # Job Statistics
    total_jobs = JobPosting.objects.count()
    active_jobs = JobPosting.objects.filter(is_active=True).count()
    total_applications = JobApplication.objects.count()
    
    # Mentorship Statistics
    total_mentors = Mentor.objects.filter(accepting_mentees=True).count()
    active_mentorships = MentorshipRequest.objects.filter(status='accepted').count()
    pending_requests = MentorshipRequest.objects.filter(status='pending').count()
    
    # Survey Statistics
    total_surveys = Survey.objects.count()
    active_surveys = Survey.objects.filter(status='active').count()
    total_responses = SurveyResponse.objects.count()
    
    # Feedback Statistics
    total_feedback = Feedback.objects.count()
    pending_feedback = Feedback.objects.filter(status='pending').count()
    
    # Recent Activity
    recent_users = User.objects.filter(date_joined__gte=seven_days_ago).order_by('-date_joined')[:5]
    recent_donations = Donation.objects.filter(
        status='completed',
        donation_date__gte=seven_days_ago
    ).select_related('campaign', 'donor').order_by('-donation_date')[:5]
    recent_events = Event.objects.filter(
        created_at__gte=seven_days_ago
    ).order_by('-created_at')[:5]
    
    context = {
        # User stats
        'total_users': total_users,
        'active_users': active_users,
        'new_users_this_month': new_users_this_month,
        
        # Alumni stats
        'total_alumni': total_alumni,
        'verified_alumni': verified_alumni,
        
        # Donation stats
        'total_donations': total_donations,
        'donation_count': donation_count,
        'active_campaigns': active_campaigns,
        
        # Event stats
        'total_events': total_events,
        'upcoming_events': upcoming_events,
        'total_rsvps': total_rsvps,
        
        # Job stats
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'total_applications': total_applications,
        
        # Mentorship stats
        'total_mentors': total_mentors,
        'active_mentorships': active_mentorships,
        'pending_requests': pending_requests,
        
        # Survey stats
        'total_surveys': total_surveys,
        'active_surveys': active_surveys,
        'total_responses': total_responses,
        
        # Feedback stats
        'total_feedback': total_feedback,
        'pending_feedback': pending_feedback,
        
        # Recent activity
        'recent_users': recent_users,
        'recent_donations': recent_donations,
        'recent_events': recent_events,
    }
    
    return render(request, 'admin/dashboard.html', context)

@login_required
def dashboard_analytics_api(request):
    """API endpoint for dashboard analytics data"""
    # Check permissions
    if not request.user.is_staff and not request.user.is_superuser:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    # Get date range from request
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # User registration data
    user_data = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        count = User.objects.filter(
            date_joined__date=date.date()
        ).count()
        user_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    
    # Donation data
    donation_data = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        amount = Donation.objects.filter(
            donation_date__date=date.date(),
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        donation_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'amount': float(amount)
        })
    
    # Event RSVP data
    rsvp_data = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        count = EventRSVP.objects.filter(
            created_at__date=date.date()
        ).count()
        rsvp_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    
    # Job application data
    application_data = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        count = JobApplication.objects.filter(
            application_date__date=date.date()
        ).count()
        application_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    
    # Alumni by graduation year
    alumni_by_year = Alumni.objects.values('graduation_year').annotate(
        count=Count('id')
    ).order_by('graduation_year')
    
    # Top campaigns by donations
    top_campaigns = Campaign.objects.annotate(
        total_donations=Sum('donations__amount', filter=Q(donations__status='completed'))
    ).order_by('-total_donations')[:5]
    
    campaign_data = []
    for campaign in top_campaigns:
        campaign_data.append({
            'name': campaign.name,
            'total': float(campaign.total_donations or 0)
        })
    
    return JsonResponse({
        'user_registrations': user_data,
        'donations': donation_data,
        'event_rsvps': rsvp_data,
        'job_applications': application_data,
        'alumni_by_year': list(alumni_by_year),
        'top_campaigns': campaign_data
    })