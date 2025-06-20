from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Count, Q, F, Avg, Sum, Case, When, IntegerField
from django.db.models.functions import TruncDate, ExtractHour
from datetime import timedelta, datetime
from alumni_groups.models import AlumniGroup
from announcements.models import Announcement
from events.models import Event, EventRSVP
from alumni_directory.models import Alumni
from feedback.models import Feedback
from core.models import UserEngagement, EngagementScore, Post, Comment, Reaction
from django.http import JsonResponse
import pandas as pd
import numpy as np
import json
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

def is_superuser(user):
    return user.is_authenticated and user.is_superuser

def home(request):
    if not request.user.is_authenticated:
        # Get the latest announcements
        try:
            from announcements.models import Announcement
            announcements = Announcement.objects.filter(
                is_active=True
            ).order_by('-date_posted')[:3]
        except ImportError:
            announcements = []
        
        # Get upcoming events
        try:
            from events.models import Event
            from django.utils import timezone
            upcoming_events = Event.objects.filter(
                start_date__gte=timezone.now(),
                status='published'
            ).order_by('start_date')[:3]
        except ImportError:
            upcoming_events = []
        
        # Get featured alumni
        try:
            from alumni_directory.models import Alumni
            featured_alumni = Alumni.objects.filter(
                is_verified=True,
                is_featured=True
            ).order_by('?')[:3]  # Random selection
            
            # If no featured alumni, just get some random verified alumni
            if not featured_alumni:
                featured_alumni = Alumni.objects.filter(
                    is_verified=True
                ).order_by('?')[:3]
        except ImportError:
            featured_alumni = []
        
        # Get statistics
        try:
            alumni_count = Alumni.objects.filter(is_verified=True).count()
        except:
            alumni_count = None
            
        try:
            from alumni_groups.models import AlumniGroup
            group_count = AlumniGroup.objects.count()
        except:
            group_count = None
            
        try:
            event_count = Event.objects.count()
        except:
            event_count = None
            
        try:
            from jobs.models import Job
            job_count = Job.objects.count()
        except:
            job_count = None
        
        context = {
            'announcements': announcements,
            'upcoming_events': upcoming_events,
            'featured_alumni': featured_alumni,
            'alumni_count': alumni_count,
            'group_count': group_count,
            'event_count': event_count,
            'job_count': job_count,
        }
        
        return render(request, 'home.html', context)
        
    if request.user.is_superuser:
        return admin_dashboard(request)
    return redirect('accounts:profile_detail')

def calculate_engagement_metrics(start_date, end_date):
    """Calculate engagement metrics for the given date range"""
    daily_users = UserEngagement.objects.filter(
        created__range=(start_date, end_date)
    ).count()

    total_posts = Post.objects.filter(
        created_at__range=(start_date, end_date)
    ).count()

    total_comments = Comment.objects.filter(
        created_at__range=(start_date, end_date)
    ).count()

    total_reactions = Reaction.objects.filter(
        created_at__range=(start_date, end_date)
    ).count()

    active_users = UserEngagement.objects.filter(
        last_activity__range=(start_date, end_date)
    ).count()

    # Calculate user segments based on engagement level
    user_engagement_counts = UserEngagement.objects.filter(
        created__range=(start_date, end_date)
    ).values('user').annotate(
        engagement_count=Count('id')
    )

    highly_active = user_engagement_counts.filter(engagement_count__gte=10).count()
    moderately_active = user_engagement_counts.filter(engagement_count__gte=5, engagement_count__lt=10).count()
    low_activity = user_engagement_counts.filter(engagement_count__lt=5).count()

    user_segments = [
        {'name': 'Highly Active', 'count': highly_active},
        {'name': 'Moderately Active', 'count': moderately_active},
        {'name': 'Low Activity', 'count': low_activity}
    ]

    # Calculate hourly activity distribution
    hourly_activity = UserEngagement.objects.filter(
        created__range=(start_date, end_date)
    ).annotate(
        hour=ExtractHour('created')
    ).values('hour').annotate(
        count=Count('id')
    ).order_by('hour')
    
    # Ensure we have data for all 24 hours (including zero values)
    hourly_activity_dict = {item['hour']: item['count'] for item in hourly_activity}
    hourly_activity_complete = []
    for hour in range(24):
        hourly_activity_complete.append({
            'hour': hour,
            'count': hourly_activity_dict.get(hour, 0)
        })

    return {
        'daily_users': daily_users,
        'total_posts': total_posts,
        'total_comments': total_comments,
        'total_reactions': total_reactions,
        'active_users': active_users,
        'user_segments': user_segments,
        'hourly_activity': hourly_activity_complete,
    }

def calculate_retention_metrics(days=30):
    """Calculate user retention metrics."""
    today = timezone.now()
    start_date = today - timedelta(days=days)
    
    # Get all users who were active in the period
    active_users = UserEngagement.objects.filter(
        created__gte=start_date
    ).values('user').distinct()
    
    # Calculate returning users (users who were active on multiple days)
    returning_users = UserEngagement.objects.filter(
        created__gte=start_date,
        user__in=active_users.values('user')
    ).annotate(
        date=TruncDate('created')
    ).values('user').annotate(
        days_active=Count('date', distinct=True)
    ).filter(days_active__gt=1).count()
    
    total_users = active_users.count()
    retention_rate = (returning_users / total_users * 100) if total_users > 0 else 0
    
    return {
        'active_users': total_users,
        'returning_users': returning_users,
        'retention_rate': round(retention_rate, 1)
    }

def calculate_growth_metrics(days=30):
    """Calculate growth metrics including user acquisition and churn."""
    today = timezone.now()
    start_date = today - timedelta(days=days)
    previous_start = start_date - timedelta(days=days)
    
    # New user signups
    current_signups = Alumni.objects.filter(
        created_at__range=(start_date, today)
    ).count()
    
    previous_signups = Alumni.objects.filter(
        created_at__range=(previous_start, start_date)
    ).count()
    
    # Calculate growth rate
    growth_rate = ((current_signups - previous_signups) / previous_signups * 100) if previous_signups > 0 else 0
    
    # Active users in both periods
    current_active = UserEngagement.objects.filter(
        created__range=(start_date, today)
    ).values('user').distinct().count()
    
    previous_active = UserEngagement.objects.filter(
        created__range=(previous_start, start_date)
    ).values('user').distinct().count()
    
    # Calculate churn rate
    churned_users = previous_active - current_active
    churn_rate = (churned_users / previous_active * 100) if previous_active > 0 else 0
    
    return {
        'new_signups': current_signups,
        'growth_rate': round(growth_rate, 1),
        'churned_users': churned_users,
        'churn_rate': round(churn_rate, 1)
    }

def calculate_event_metrics(days=30):
    """Calculate detailed event engagement metrics."""
    today = timezone.now()
    start_date = today - timedelta(days=days)
    
    # Event participation stats
    events = Event.objects.filter(start_date__range=(start_date, today))
    total_events = events.count()
    
    participation_stats = EventRSVP.objects.filter(
        event__in=events
    ).aggregate(
        attending=Count(Case(When(status='yes', then=1))),
        maybe=Count(Case(When(status='maybe', then=1))),
        declined=Count(Case(When(status='no', then=1)))
    )
    
    total_responses = sum(participation_stats.values())
    response_rate = (total_responses / (total_events * Alumni.objects.count()) * 100) if total_events > 0 else 0
    
    # Event type distribution (using status and virtual/in-person)
    type_distribution = []
    
    # Status distribution
    status_counts = events.values('status').annotate(count=Count('id')).order_by('-count')
    for status_data in status_counts:
        type_distribution.append({
            'category': dict(Event.STATUS_CHOICES)[status_data['status']],
            'count': status_data['count']
        })
    
    # Virtual vs In-person distribution
    virtual_count = events.filter(is_virtual=True).count()
    in_person_count = events.filter(is_virtual=False).count()
    type_distribution.extend([
        {'category': 'Virtual Events', 'count': virtual_count},
        {'category': 'In-Person Events', 'count': in_person_count}
    ])
    
    return {
        'total_events': total_events,
        'participation_stats': participation_stats,
        'response_rate': round(response_rate, 1),
        'category_distribution': type_distribution
    }

@user_passes_test(is_superuser)
def admin_dashboard(request):
    """
    Combined admin dashboard with analytics for alumni engagement data.
    """
    today = timezone.now()
    thirty_days_ago = today - timedelta(days=30)
    
    # Basic statistics - actual counts
    total_alumni = Alumni.objects.filter(is_verified=True).count()
    total_groups = AlumniGroup.objects.count()
    total_events = Event.objects.count()
    total_feedback = Feedback.objects.count()
    
    # Calculate industry distribution
    industry_distribution = Alumni.objects.filter(is_verified=True).values('industry').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Convert to percentage and format for the template
    industry_data = []
    total_with_industry = sum(ind['count'] for ind in industry_distribution if ind['industry'])

    for industry in industry_distribution:
        if industry['industry']:  # Only include non-null industries
            percentage = (industry['count'] / total_with_industry * 100) if total_with_industry > 0 else 0
            industry_data.append({
                'industry': industry['industry'],
                'percentage': round(percentage, 1)
            })

    # If there are no industries or all are null, provide a default "Not Specified" category
    if not industry_data:
        industry_data = [{
            'industry': 'Not Specified',
            'percentage': 100.0
        }]
    
    # Calculate graduation year distribution
    current_year = today.year
    grad_ranges = [
        {'name': '2010-2015', 'start': 2010, 'end': 2015, 'count': 0},
        {'name': '2016-2020', 'start': 2016, 'end': 2020, 'count': 0},
        {'name': '2021-Present', 'start': 2021, 'end': current_year, 'count': 0}
    ]
    
    # Query graduation years and count per range
    graduation_years = Alumni.objects.filter(is_verified=True).values('graduation_year').exclude(graduation_year__isnull=True)
    
    # Count alumni in each graduation year range
    for range_data in grad_ranges:
        range_count = graduation_years.filter(
            graduation_year__gte=range_data['start'],
            graduation_year__lte=range_data['end']
        ).count()
        range_data['count'] = range_count
    
    # Calculate percentages for each range
    total_with_grad_year = sum(r['count'] for r in grad_ranges)
    for range_data in grad_ranges:
        range_data['percentage'] = round((range_data['count'] / total_with_grad_year * 100), 1) if total_with_grad_year > 0 else 0
    
    # If no graduation years are specified, create a default
    if total_with_grad_year == 0:
        for range_data in grad_ranges:
            if range_data['name'] == '2021-Present':
                range_data['percentage'] = 100.0
            else:
                range_data['percentage'] = 0.0

    # Calculate location distribution
    location_distribution = Alumni.objects.filter(is_verified=True).values('province').annotate(
        count=Count('id')
    ).order_by('-count')

    # Convert to percentage and format for the template
    location_data = []
    total_with_location = sum(loc['count'] for loc in location_distribution if loc['province'])

    for location in location_distribution:
        if location['province']:  # Only include non-null provinces
            percentage = (location['count'] / total_with_location * 100) if total_with_location > 0 else 0
            location_data.append({
                'location': location['province'],
                'percentage': round(percentage, 1)
            })

    # If there are no locations or all are null, provide a default "Not Specified" category
    if not location_data:
        location_data = [{
            'location': 'Not Specified',
            'percentage': 100.0
        }]

    # Calculate employment status distribution
    employment_distribution = Alumni.objects.filter(is_verified=True).values('employment_status').annotate(
        count=Count('id')
    ).order_by('-count')

    # Convert to percentage and format for the template
    employment_data = []
    total_with_employment = sum(emp['count'] for emp in employment_distribution if emp['employment_status'])

    for employment in employment_distribution:
        if employment['employment_status']:  # Only include non-null employment statuses
            percentage = (employment['count'] / total_with_employment * 100) if total_with_employment > 0 else 0
            # Get the display name for the employment status
            status_display = dict(Alumni.EMPLOYMENT_STATUS_CHOICES).get(employment['employment_status'], employment['employment_status'])
            employment_data.append({
                'status': status_display,
                'percentage': round(percentage, 1)
            })

    # If there are no employment statuses or all are null, provide a default "Not Specified" category
    if not employment_data:
        employment_data = [{
            'status': 'Not Specified',
            'percentage': 100.0
        }]
    
    # Active groups - groups with recent activity
    active_groups = AlumniGroup.objects.filter(
        Q(events__start_date__gte=thirty_days_ago) |
        Q(discussions__updated_at__gte=thirty_days_ago) |
        Q(updated_at__gte=thirty_days_ago)
    ).distinct().count()
    
    # Get active users in last 30 days - actual engagement
    active_users_30d = UserEngagement.objects.filter(
        created__gte=thirty_days_ago
    ).values('user').distinct().count()
    
    # Calculate event participation rate with actual RSVPs
    recent_events = Event.objects.filter(start_date__gte=thirty_days_ago)
    total_rsvps = EventRSVP.objects.filter(event__in=recent_events, status='attending').count()
    event_participation_rate = round((total_rsvps / total_alumni * 100), 1) if total_alumni > 0 else 0
    
    # Calculate feedback response rate based on actual feedback
    feedback_responses = Feedback.objects.filter(created_at__gte=thirty_days_ago).count()
    feedback_response_rate = round((feedback_responses / total_alumni * 100), 1) if total_alumni > 0 else 0
    
    # Calculate user segments based on actual engagement scores
    user_segments = {
        'highly_engaged': Alumni.objects.filter(user__engagement_score__total_points__gte=50).count(),
        'moderately_engaged': Alumni.objects.filter(user__engagement_score__total_points__gte=20, user__engagement_score__total_points__lt=50).count(),
        'low_engaged': Alumni.objects.filter(user__engagement_score__total_points__gt=0, user__engagement_score__total_points__lt=20).count(),
        'inactive': Alumni.objects.filter(Q(user__engagement_score__total_points=0) | Q(user__engagement_score__isnull=True)).count()
    }
    
    # Get recent announcements
    recent_announcements = Announcement.objects.order_by('-date_posted')[:5]
    
    # Get upcoming events
    upcoming_events = Event.objects.filter(
        start_date__gte=today
    ).order_by('start_date')[:5]
    
    # Get recent feedback
    recent_feedback = Feedback.objects.order_by('-created_at')[:5]
    
    # Get job metrics from the JobPosting model
    try:
        from jobs.models import JobPosting
        
        # Calculate job board metrics
        featured_jobs = JobPosting.objects.filter(is_featured=True).count()
        manual_jobs = JobPosting.objects.filter(source='manual').count()
        scraped_jobs = JobPosting.objects.filter(source='indeed').count()
        jobs_this_month = JobPosting.objects.filter(posted_date__gte=thirty_days_ago).count()
    except (ImportError, ModuleNotFoundError):
        featured_jobs = 0
        manual_jobs = 0
        scraped_jobs = 0
        jobs_this_month = 0
    
    # Calculate actual engagement metrics
    engagement_metrics = {
        'daily_users': UserEngagement.objects.filter(created__date=today.date()).values('user').distinct().count(),
        'active_users': active_users_30d,
        'total_posts': Post.objects.filter(created_at__gte=thirty_days_ago).count(),
        'total_comments': Comment.objects.filter(created_at__gte=thirty_days_ago).count(),
        'total_reactions': Reaction.objects.filter(created_at__gte=thirty_days_ago).count()
    }
    
    # Calculate actual retention metrics
    retention_metrics = calculate_retention_metrics()
    
    # Calculate actual growth metrics
    growth_metrics = calculate_growth_metrics()
    
    # Calculate actual event metrics
    event_metrics = calculate_event_metrics()
    
    # Calculate registration growth trend
    registration_trend = []
    for i in range(7):
        date = today - timedelta(days=i*30)
        count = Alumni.objects.filter(
            created_at__year=date.year,
            created_at__month=date.month
        ).count()
        registration_trend.append({
            'month': date.strftime('%b'),
            'count': count
        })
    registration_trend.reverse()
    
    # Prepare chart data with more explicit serialization
    registration_trend = [
        {'month': item['month'], 'count': item['count']} 
        for item in registration_trend
    ]
    
    industry_distribution = [
        {'industry': item['industry'], 'percentage': item['percentage']} 
        for item in industry_data
    ]
    
    graduation_year_distribution = [
        {'name': item['name'], 'percentage': item['percentage']} 
        for item in grad_ranges
    ]
    
    # Update context with prepared data
    context = {
        # Analytics data
        'total_users': total_alumni,
        'total_events': total_events,
        'total_feedback': total_feedback,
        'active_groups': active_groups,
        'active_users_30d': active_users_30d,
        'event_participation_rate': event_participation_rate,
        'feedback_response_rate': feedback_response_rate,
        'user_segments': user_segments,
        'industry_distribution': industry_distribution,
        'graduation_year_distribution': graduation_year_distribution,
        'registration_trend_json': json.dumps(registration_trend),
        'industry_distribution_json': json.dumps(industry_distribution),
        'graduation_year_distribution_json': json.dumps(graduation_year_distribution),
        'location_distribution_json': json.dumps(location_data),
        'employment_status_json': json.dumps(employment_data),
        
        # Dashboard data
        'recent_announcements': recent_announcements,
        'upcoming_events': upcoming_events,
        'recent_feedback': recent_feedback,
        'total_groups': total_groups,
        'daily_active_users': engagement_metrics['daily_users'],
        'monthly_active_users': engagement_metrics['active_users'],
        'total_posts': engagement_metrics['total_posts'],
        'total_comments': engagement_metrics['total_comments'],
        'total_reactions': engagement_metrics['total_reactions'],
        'engagement_rate': round((active_users_30d / total_alumni * 100), 1) if total_alumni > 0 else 0,
        'retention_rate': retention_metrics['retention_rate'],
        'churn_rate': growth_metrics['churn_rate'],
        'event_response_rate': event_metrics['response_rate'],
        'event_participation_stats': event_metrics['participation_stats'],
        'event_categories': json.dumps([{'category': str(cat['category']), 'count': cat['count']} for cat in event_metrics['category_distribution']]),
        'featured_jobs': featured_jobs,
        'manual_jobs': manual_jobs,
        'scraped_jobs': scraped_jobs,
        'jobs_this_month': jobs_this_month,
    }
    
    return render(request, 'admin/analytics_dashboard.html', context)

@login_required
@user_passes_test(is_superuser)
def engagement_data_api(request):
    """API endpoint to fetch engagement data for different time periods."""
    period = request.GET.get('period', '30')  # Default to 30 days
    try:
        days = int(period)
    except ValueError:
        days = 30

    today = timezone.now()
    start_date = today - timedelta(days=days)
    
    # Get engagement metrics for the period
    metrics = calculate_engagement_metrics(start_date, today)
    
    return JsonResponse(metrics)

# The analytics_dashboard function has been merged with admin_dashboard
# and is no longer needed 

def search(request):
    """
    Global search functionality for the alumni system.
    Searches across alumni, groups, events, announcements, etc.
    """
    query = request.GET.get('q', '')
    results = {
        'query': query,
        'alumni': [],
        'groups': [],
        'events': [],
        'announcements': [],
        'jobs': []
    }
    
    if query:
        # Search for alumni
        alumni_results = Alumni.objects.filter(
            Q(user__first_name__icontains=query) | 
            Q(user__last_name__icontains=query) |
            Q(user__email__icontains=query) |
            Q(bio__icontains=query) |
            Q(industry__icontains=query)
        )[:10]
        results['alumni'] = alumni_results
        
        # Search for groups
        from alumni_groups.models import AlumniGroup
        group_results = AlumniGroup.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )[:10]
        results['groups'] = group_results
        
        # Search for events
        event_results = Event.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query)
        )[:10]
        results['events'] = event_results
        
        # Search for announcements
        announcement_results = Announcement.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query)
        )[:10]
        results['announcements'] = announcement_results
        
        # Search for jobs
        try:
            from jobs.models import Job
            job_results = Job.objects.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(company__icontains=query) |
                Q(location__icontains=query)
            )[:10]
            results['jobs'] = job_results
        except ImportError:
            # Jobs app might not be installed
            pass
    
    return render(request, 'core/search_results.html', {'results': results})

@login_required
def go_to_profile(request):
    """
    Redirects the user to their profile page.
    This is a convenience view for navigation links.
    """
    return redirect('accounts:profile_detail') 