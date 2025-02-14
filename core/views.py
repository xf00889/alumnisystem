from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta, datetime
from alumni_groups.models import AlumniGroup
from announcements.models import Announcement
from events.models import Event, EventRSVP
from alumni_directory.models import Alumni

User = get_user_model()

def is_superuser(user):
    return user.is_authenticated and user.is_superuser

def home(request):
    if not request.user.is_authenticated:
        return render(request, 'home.html')
    if request.user.is_superuser:
        return admin_dashboard(request)
    # Redirect regular authenticated users to home or profile page
    return redirect('accounts:profile_detail')

@user_passes_test(is_superuser)
def admin_dashboard(request):
    today = timezone.now()
    thirty_days_ago = today - timedelta(days=30)
    
    # Basic statistics
    total_users = User.objects.count()
    total_groups = AlumniGroup.objects.count()
    active_groups = AlumniGroup.objects.filter(
        Q(events__start_date__gte=thirty_days_ago) |
        Q(messages__created_at__gte=thirty_days_ago)
    ).distinct().count()
    
    # User growth rate
    last_month_users = User.objects.filter(date_joined__lt=thirty_days_ago).count()
    user_growth = total_users - last_month_users
    user_growth_rate = round((user_growth / last_month_users * 100), 1) if last_month_users > 0 else 100
    
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
    total_possible = recent_events.count() * User.objects.count()
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
    last_month_possible = last_month_events.count() * last_month_users
    last_month_participation = (last_month_rsvps / last_month_possible * 100) if last_month_possible > 0 else 0
    participation_growth = round(event_participation_rate - last_month_participation, 1)
    
    # Group growth
    last_month_active_groups = AlumniGroup.objects.filter(
        Q(events__start_date__gte=thirty_days_ago - timedelta(days=30), events__start_date__lt=thirty_days_ago) |
        Q(messages__created_at__gte=thirty_days_ago - timedelta(days=30), messages__created_at__lt=thirty_days_ago)
    ).distinct().count()
    group_growth = round(((active_groups - last_month_active_groups) / last_month_active_groups * 100), 1) if last_month_active_groups > 0 else 100
    
    # Employment distribution data - Get real data from Alumni model
    employment_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    employment_data = {
        'employed': [
            Alumni.objects.filter(employment_status='EMPLOYED', updated_at__month=i).count()
            for i in range(1, 7)
        ],
        'unemployed': [
            Alumni.objects.filter(employment_status='UNEMPLOYED', updated_at__month=i).count()
            for i in range(1, 7)
        ]
    }
    
    # Department distribution data - Get real data from Alumni model
    department_labels = ['Computer Science', 'Engineering', 'Business', 'Arts', 'Medicine']
    department_data = [
        Alumni.objects.filter(course__icontains=dept).count()
        for dept in department_labels
    ]
    
    # Event participation trend
    event_participation_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    event_participation_data = [45, 52, 58, 60, 65, 70]
    
    # Group activity data
    group_activity = AlumniGroup.objects.annotate(
        total_members=Count('memberships'),
        total_events=Count('events'),
        total_messages=Count('messages')
    ).order_by('-total_members')[:5]
    
    group_activity_labels = [group.name for group in group_activity]
    group_activity_data = [group.total_members for group in group_activity]
    
    # Recent activities
    recent_activities = []
    
    # Recent user registrations
    recent_users = User.objects.order_by('-date_joined')[:3]
    for user in recent_users:
        recent_activities.append({
            'title': f"New alumni registered: {user.get_full_name() or user.username}",
            'timestamp': user.date_joined,
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
    
    # Sort activities by timestamp
    recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activities = recent_activities[:5]

    context = {
        'total_users': total_users,
        'user_growth_rate': user_growth_rate,
        'employment_rate': employment_rate,
        'employment_growth': employment_growth,
        'event_participation_rate': event_participation_rate,
        'participation_growth': participation_growth,
        'active_groups': active_groups,
        'group_growth': group_growth,
        'employed_count': employed_count,
        'unemployed_count': unemployed_count,
        'employment_labels': employment_labels,
        'employment_data': employment_data,
        'department_labels': department_labels,
        'department_data': department_data,
        'event_participation_labels': event_participation_labels,
        'event_participation_data': event_participation_data,
        'group_activity_labels': group_activity_labels,
        'group_activity_data': group_activity_data,
        'recent_activities': recent_activities,
    }

    return render(request, 'admin/dashboard.html', context) 