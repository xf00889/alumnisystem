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

    # For authenticated users, show the authenticated home page instead of redirecting
    # This prevents redirect loops if profile_detail fails
    if request.user.is_superuser:
        return redirect('core:admin_dashboard')  # Use consistent redirect target

    # Show authenticated home page instead of redirecting to profile
    # This prevents redirect loops and provides a better user experience
    try:
        from announcements.models import Announcement
        announcements = Announcement.objects.filter(
            is_active=True
        ).order_by('-date_posted')[:5]
    except ImportError:
        announcements = []

    try:
        from events.models import Event
        from django.utils import timezone
        upcoming_events = Event.objects.filter(
            start_date__gte=timezone.now(),
            status='published'
        ).order_by('start_date')[:5]
    except ImportError:
        upcoming_events = []

    context = {
        'announcements': announcements,
        'upcoming_events': upcoming_events,
        'user': request.user,
    }

    return render(request, 'authenticated_home.html', context)

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