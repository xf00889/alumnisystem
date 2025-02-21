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
from core.models import UserEngagement, EngagementScore
from django.http import JsonResponse
import pandas as pd
import numpy as np

User = get_user_model()

def is_superuser(user):
    return user.is_authenticated and user.is_superuser

def home(request):
    if not request.user.is_authenticated:
        return render(request, 'home.html')
    if request.user.is_superuser:
        return admin_dashboard(request)
    return redirect('accounts:profile_detail')

def calculate_engagement_metrics(start_date, end_date):
    """Calculate detailed engagement metrics for a given date range."""
    
    # Daily active users
    daily_users = UserEngagement.objects.filter(
        created__range=(start_date, end_date)
    ).annotate(
        date=TruncDate('created')
    ).values('date').annotate(
        count=Count('user', distinct=True)
    ).order_by('date')
    
    # Hourly activity distribution
    hourly_activity = UserEngagement.objects.filter(
        created__range=(start_date, end_date)
    ).annotate(
        hour=ExtractHour('created')
    ).values('hour').annotate(
        count=Count('id')
    ).order_by('hour')
    
    # Activity type distribution
    activity_types = UserEngagement.objects.filter(
        created__range=(start_date, end_date)
    ).values('activity_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # User segments based on engagement level
    user_segments = EngagementScore.objects.filter(
        last_activity__range=(start_date, end_date)
    ).aggregate(
        highly_engaged=Count(Case(When(total_points__gte=1000, then=1))),
        moderately_engaged=Count(Case(When(total_points__range=(500, 999), then=1))),
        low_engaged=Count(Case(When(total_points__range=(100, 499), then=1))),
        inactive=Count(Case(When(total_points__lt=100, then=1)))
    )
    
    return {
        'daily_users': daily_users,
        'hourly_activity': hourly_activity,
        'activity_types': activity_types,
        'user_segments': user_segments
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
    today = timezone.now()
    thirty_days_ago = today - timedelta(days=30)
    ninety_days_ago = today - timedelta(days=90)
    
    # Get all the metrics
    engagement_metrics = calculate_engagement_metrics(thirty_days_ago, today)
    retention_metrics = calculate_retention_metrics()
    growth_metrics = calculate_growth_metrics()
    event_metrics = calculate_event_metrics()
    
    # Basic statistics
    total_alumni = Alumni.objects.filter(is_verified=True).count()
    total_groups = AlumniGroup.objects.count()
    
    # Active groups - groups with recent activity
    active_groups = AlumniGroup.objects.filter(
        Q(events__start_date__gte=thirty_days_ago) |
        Q(discussions__updated_at__gte=thirty_days_ago) |
        Q(updated_at__gte=thirty_days_ago)
    ).distinct().count()
    
    # Alumni growth rate
    last_month_alumni = Alumni.objects.filter(is_verified=True, created_at__lt=thirty_days_ago).count()
    alumni_growth = total_alumni - last_month_alumni
    alumni_growth_rate = round((alumni_growth / last_month_alumni * 100), 1) if last_month_alumni > 0 else 100
    
    # Employment statistics
    employed_count = Alumni.objects.filter(employment_status='EMPLOYED').count()
    unemployed_count = Alumni.objects.filter(employment_status='UNEMPLOYED').count()
    total_with_status = employed_count + unemployed_count
    employment_rate = round((employed_count / total_with_status * 100), 1) if total_with_status > 0 else 0
    
    # Last month employment stats for growth calculation
    last_month_employed = Alumni.objects.filter(
        employment_status='EMPLOYED',
        updated_at__lt=thirty_days_ago
    ).count()
    last_month_total = Alumni.objects.filter(
        updated_at__lt=thirty_days_ago
    ).exclude(employment_status='').count()
    last_month_rate = (last_month_employed / last_month_total * 100) if last_month_total > 0 else 0
    employment_growth = round(employment_rate - last_month_rate, 1)
    
    # Event participation
    recent_events = Event.objects.filter(start_date__gte=thirty_days_ago)
    total_rsvps = EventRSVP.objects.filter(event__in=recent_events, status='attending').count()
    total_possible = recent_events.count() * total_alumni
    event_participation_rate = round((total_rsvps / total_possible * 100), 1) if total_possible > 0 else 0
    
    # Last month event participation for growth calculation
    last_month_events = Event.objects.filter(
        start_date__gte=thirty_days_ago - timedelta(days=30),
        start_date__lt=thirty_days_ago
    )
    last_month_rsvps = EventRSVP.objects.filter(
        event__in=last_month_events,
        status='attending'
    ).count()
    last_month_possible = last_month_events.count() * last_month_alumni
    last_month_participation = (last_month_rsvps / last_month_possible * 100) if last_month_possible > 0 else 0
    participation_growth = round(event_participation_rate - last_month_participation, 1)
    
    # Group growth
    last_month_active_groups = AlumniGroup.objects.filter(
        Q(events__start_date__gte=thirty_days_ago - timedelta(days=30), events__start_date__lt=thirty_days_ago) |
        Q(discussions__updated_at__gte=thirty_days_ago - timedelta(days=30), discussions__updated_at__lt=thirty_days_ago) |
        Q(updated_at__gte=thirty_days_ago - timedelta(days=30), updated_at__lt=thirty_days_ago)
    ).distinct().count()
    group_growth = round(((active_groups - last_month_active_groups) / last_month_active_groups * 100), 1) if last_month_active_groups > 0 else 100
    
    # Employment distribution data - Last 6 months
    months = []
    employed_data = []
    unemployed_data = []
    
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30 * i)
        month_start = month_date.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        months.append(month_date.strftime('%b'))
        employed_data.append(
            Alumni.objects.filter(
                employment_status='EMPLOYED',
                updated_at__range=(month_start, month_end)
            ).count()
        )
        unemployed_data.append(
            Alumni.objects.filter(
                employment_status='UNEMPLOYED',
                updated_at__range=(month_start, month_end)
            ).count()
        )
    
    # Department distribution data
    departments = Alumni.objects.values('course').annotate(
        count=Count('id')
    ).order_by('-count')[:8]
    
    department_labels = [dept['course'] for dept in departments]
    department_data = [dept['count'] for dept in departments]
    
    # Event participation trend - Last 6 months
    event_months = []
    participation_data = []
    
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30 * i)
        month_start = month_date.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_events = Event.objects.filter(start_date__range=(month_start, month_end))
        month_rsvps = EventRSVP.objects.filter(
            event__in=month_events,
            status='attending'
        ).count()
        month_possible = month_events.count() * Alumni.objects.filter(created_at__lte=month_end).count()
        
        event_months.append(month_date.strftime('%b'))
        participation_rate = round((month_rsvps / month_possible * 100), 1) if month_possible > 0 else 0
        participation_data.append(participation_rate)
    
    # Group activity data - Most active groups
    group_activity = AlumniGroup.objects.annotate(
        total_approved_members=Count('memberships', filter=Q(memberships__status='APPROVED')),
        total_events=Count('events'),
        total_discussions=Count('discussions'),
        activity_score=F('total_approved_members') + F('total_events') + F('total_discussions')
    ).order_by('-activity_score')[:5]
    
    group_activity_labels = [group.name for group in group_activity]
    group_activity_data = [group.activity_score for group in group_activity]
    
    # Recent activities
    recent_activities = []
    
    # Recent alumni registrations
    recent_alumni = Alumni.objects.order_by('-created_at')[:3]
    for alumni in recent_alumni:
        recent_activities.append({
            'title': f"New alumni registered: {alumni.user.get_full_name() or alumni.user.username}",
            'timestamp': alumni.created_at,
            'icon': 'fa-user-plus',
            'color': '#4e73df'
        })
    
    # Recent events
    recent_events = Event.objects.order_by('-created_at')[:3]
    for event in recent_events:
        recent_activities.append({
            'title': f"New event created: {event.title}",
            'timestamp': event.created_at,
            'icon': 'fa-calendar-plus',
            'color': '#1cc88a'
        })
    
    # Recent group creations
    recent_groups = AlumniGroup.objects.order_by('-created_at')[:3]
    for group in recent_groups:
        recent_activities.append({
            'title': f"New group created: {group.name}",
            'timestamp': group.created_at,
            'icon': 'fa-users',
            'color': '#f6c23e'
        })
    
    # Recent feedback submissions
    recent_feedback = Feedback.objects.order_by('-created_at')[:3]
    for feedback in recent_feedback:
        recent_activities.append({
            'title': f"New feedback received: {feedback.subject}",
            'timestamp': feedback.created_at,
            'icon': 'fa-comment-dots',
            'color': '#e74a3b'
        })
    
    # Sort activities by timestamp and get the most recent 5
    recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activities = recent_activities[:5]

    # Engagement Analytics
    engagement_dates = []
    daily_active_users = []
    daily_engagement_scores = []
    
    for i in range(30, -1, -1):
        date = today - timedelta(days=i)
        engagement_dates.append(date.strftime('%b %d'))
        
        # Daily active users
        active_users = UserEngagement.objects.filter(
            created__date=date.date()
        ).values('user').distinct().count()
        daily_active_users.append(active_users)
        
        # Daily average engagement score
        avg_score = EngagementScore.objects.filter(
            last_activity__date=date.date()
        ).aggregate(Avg('total_points'))['total_points__avg'] or 0
        daily_engagement_scores.append(round(avg_score, 1))

    # Top engaged users
    top_engaged_users = Alumni.objects.filter(
        user__engagement_score__isnull=False
    ).select_related(
        'user__engagement_score'
    ).order_by(
        '-user__engagement_score__total_points'
    )[:10]

    # Activity distribution
    activity_distribution = []
    total_activities = UserEngagement.objects.filter(
        created__gte=thirty_days_ago
    ).count()

    for activity_type, _ in UserEngagement.ACTIVITY_TYPES:
        count = UserEngagement.objects.filter(
            created__gte=thirty_days_ago,
            activity_type=activity_type
        ).count()
        percentage = (count / total_activities * 100) if total_activities > 0 else 0
        
        activity_distribution.append({
            'type': dict(UserEngagement.ACTIVITY_TYPES)[activity_type],
            'count': count,
            'percentage': round(percentage, 1)
        })

    # Calculate average engagement score and growth rate
    current_avg_score = EngagementScore.objects.aggregate(
        Avg('total_points')
    )['total_points__avg'] or 0
    
    last_month_avg_score = EngagementScore.objects.filter(
        last_activity__lt=thirty_days_ago
    ).aggregate(
        Avg('total_points')
    )['total_points__avg'] or 0
    
    engagement_growth_rate = (
        ((current_avg_score - last_month_avg_score) / last_month_avg_score * 100)
        if last_month_avg_score > 0 else 0
    )

    # Total interactions in last 30 days
    total_interactions_30d = UserEngagement.objects.filter(
        created__gte=thirty_days_ago
    ).count()

    # Update context with new metrics
    context = {
        'total_users': total_alumni,
        'user_growth_rate': alumni_growth_rate,
        'employment_rate': employment_rate,
        'employment_growth': employment_growth,
        'event_participation_rate': event_participation_rate,
        'participation_growth': participation_growth,
        'active_groups': active_groups,
        'group_growth': group_growth,
        'employed_count': employed_count,
        'unemployed_count': unemployed_count,
        'employment_labels': months,
        'employment_data': {
            'employed': employed_data,
            'unemployed': unemployed_data
        },
        'department_labels': department_labels,
        'department_data': department_data,
        'event_participation_labels': event_months,
        'event_participation_data': participation_data,
        'group_activity_labels': group_activity_labels,
        'group_activity_data': group_activity_data,
        'recent_activities': recent_activities,
        'active_users_30d': UserEngagement.objects.filter(
            created__gte=thirty_days_ago
        ).values('user').distinct().count(),
        'engagement_dates': engagement_dates,
        'daily_active_users': daily_active_users,
        'daily_engagement_scores': daily_engagement_scores,
        'top_engaged_users': top_engaged_users,
        'activity_distribution': activity_distribution,
        'activity_types': [item['type'] for item in activity_distribution],
        'activity_counts': [item['count'] for item in activity_distribution],
        'avg_engagement_score': round(current_avg_score, 1),
        'engagement_growth_rate': round(engagement_growth_rate, 1),
        'total_interactions_30d': total_interactions_30d,
        'user_segments': engagement_metrics['user_segments'],
        'hourly_activity': list(engagement_metrics['hourly_activity']),
        'retention_rate': retention_metrics['retention_rate'],
        'returning_users': retention_metrics['returning_users'],
        'new_signups': growth_metrics['new_signups'],
        'churn_rate': growth_metrics['churn_rate'],
        'event_response_rate': event_metrics['response_rate'],
        'event_participation_stats': event_metrics['participation_stats'],
        'event_categories': list(event_metrics['category_distribution']),
    }

    return render(request, 'admin/dashboard.html', context)

@login_required
@user_passes_test(is_superuser)
def engagement_data_api(request):
    """API endpoint to fetch engagement data for different time periods."""
    period = request.GET.get('period', '30')  # Default to 30 days
    try:
        days = int(period)
    except ValueError:
        return JsonResponse({'error': 'Invalid period'}, status=400)

    today = timezone.now()
    start_date = today - timedelta(days=days)
    
    # Prepare date range
    dates = []
    active_users = []
    engagement_scores = []
    
    for i in range(days, -1, -1):
        date = today - timedelta(days=i)
        dates.append(date.strftime('%b %d'))
        
        # Daily active users
        active_count = UserEngagement.objects.filter(
            created__date=date.date()
        ).values('user').distinct().count()
        active_users.append(active_count)
        
        # Daily average engagement score
        avg_score = EngagementScore.objects.filter(
            last_activity__date=date.date()
        ).aggregate(Avg('total_points'))['total_points__avg'] or 0
        engagement_scores.append(round(avg_score, 1))

    return JsonResponse({
        'dates': dates,
        'active_users': active_users,
        'engagement_scores': engagement_scores
    }) 