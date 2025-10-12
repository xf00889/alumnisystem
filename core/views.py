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
from core.models import UserEngagement, EngagementScore, Post, Comment, Reaction, Notification
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from django.views import View
from django import forms
from django.core.exceptions import ValidationError
import pandas as pd
import numpy as np
import json
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

def is_superuser(user):
    return user.is_authenticated and user.is_superuser

def home(request):
    # Handle authenticated users
    if request.user.is_authenticated:
        # Check if user is superuser
        if request.user.is_superuser:
            return redirect('core:admin_dashboard')
        
        # Ensure user has a profile
        from accounts.models import Profile
        profile, created = Profile.objects.get_or_create(user=request.user)
        
        # Check if user has completed registration
        if not profile.has_completed_registration:
            return redirect('accounts:post_registration')
        
        # Show authenticated home page for users who have completed registration
        try:
            from announcements.models import Announcement
            announcements = Announcement.objects.filter(
                is_active=True
            ).order_by('-date_posted')[:5]
        except (ImportError, Exception) as e:
            logger.error(f"Error fetching announcements for authenticated user: {e}")
            announcements = []

        try:
            from events.models import Event
            from django.utils import timezone
            upcoming_events = Event.objects.filter(
                start_date__gte=timezone.now(),
                status='published'
            ).order_by('start_date')[:5]
        except (ImportError, Exception) as e:
            logger.error(f"Error fetching events for authenticated user: {e}")
            upcoming_events = []

        context = {
            'announcements': announcements,
            'upcoming_events': upcoming_events,
            'user': request.user,
        }

        return render(request, 'authenticated_home.html', context)
    
    # Handle unauthenticated users
    # Get the latest announcements
    try:
        from announcements.models import Announcement
        announcements = Announcement.objects.filter(
            is_active=True
        ).order_by('-date_posted')[:3]
    except (ImportError, Exception) as e:
        logger.error(f"Error fetching announcements: {e}")
        announcements = []

    # Get upcoming events
    try:
        from events.models import Event
        from django.utils import timezone
        upcoming_events = Event.objects.filter(
            start_date__gte=timezone.now(),
            status='published'
        ).order_by('start_date')[:3]
    except (ImportError, Exception) as e:
        logger.error(f"Error fetching upcoming events: {e}")
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
    except (ImportError, Exception) as e:
        logger.error(f"Error fetching featured alumni: {e}")
        featured_alumni = []

    # Get statistics
    try:
        alumni_count = Alumni.objects.filter(is_verified=True).count()
    except Exception as e:
        logger.error(f"Error fetching alumni count: {e}")
        alumni_count = None

    try:
        from alumni_groups.models import AlumniGroup
        group_count = AlumniGroup.objects.count()
    except Exception as e:
        logger.error(f"Error fetching group count: {e}")
        group_count = None

    try:
        event_count = Event.objects.count()
    except Exception as e:
        logger.error(f"Error fetching event count: {e}")
        event_count = None

    try:
        from jobs.models import JobPosting
        job_count = JobPosting.objects.filter(is_active=True).count()
    except Exception as e:
        logger.error(f"Error fetching job count: {e}")
        job_count = 0

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


# Notification Views
@login_required
@require_http_methods(["GET"])
def get_notifications(request):
    """
    API endpoint to fetch notifications for the current user
    """
    try:
        # Get query parameters
        limit = int(request.GET.get('limit', 10))
        offset = int(request.GET.get('offset', 0))
        unread_only = request.GET.get('unread_only', 'false').lower() == 'true'

        # Build query
        notifications_query = Notification.objects.filter(recipient=request.user)

        if unread_only:
            notifications_query = notifications_query.filter(is_read=False)

        # Get notifications with pagination
        notifications = notifications_query[offset:offset + limit]

        # Serialize notifications
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'notification_type': notification.notification_type,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat(),
                'action_url': notification.action_url,
                'sender': {
                    'name': notification.sender.get_full_name() if notification.sender else None,
                    'avatar': notification.sender.profile.avatar.url if notification.sender and notification.sender.profile.avatar else None
                } if notification.sender else None
            })

        # Get total count and unread count
        total_count = Notification.objects.filter(recipient=request.user).count()
        unread_count = Notification.get_unread_count(request.user)

        return JsonResponse({
            'success': True,
            'notifications': notifications_data,
            'total_count': total_count,
            'unread_count': unread_count,
            'has_more': (offset + limit) < total_count
        })

    except Exception as e:
        logger.error(f"Error fetching notifications: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to fetch notifications'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """
    API endpoint to mark a specific notification as read
    """
    try:
        notification = Notification.objects.get(
            id=notification_id,
            recipient=request.user
        )
        notification.mark_as_read()

        return JsonResponse({
            'success': True,
            'unread_count': Notification.get_unread_count(request.user)
        })

    except Notification.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Notification not found'
        }, status=404)
    except Exception as e:
        logger.error(f"Error marking notification as read: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to mark notification as read'
        }, status=500)


@login_required
@require_http_methods(["POST"])
def mark_all_notifications_read(request):
    """
    API endpoint to mark all notifications as read for the current user
    """
    try:
        Notification.mark_all_as_read(request.user)

        return JsonResponse({
            'success': True,
            'unread_count': 0
        })

    except Exception as e:
        logger.error(f"Error marking all notifications as read: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to mark all notifications as read'
        }, status=500)


@login_required
@require_http_methods(["GET"])
def get_unread_count(request):
    """
    API endpoint to get unread notification count for the current user
    """
    try:
        unread_count = Notification.get_unread_count(request.user)

        return JsonResponse({
            'success': True,
            'unread_count': unread_count
        })

    except Exception as e:
        logger.error(f"Error getting unread count: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to get unread count'
        }, status=500)


# Landing Page Views for Unauthenticated Users

def landing_events(request):
    """
    Display published events for unauthenticated users with pagination
    """
    events_list = Event.objects.filter(
        status='published',
        start_date__gte=timezone.now()
    ).order_by('start_date')

    paginator = Paginator(events_list, 9)  # Show 9 events per page
    page_number = request.GET.get('page')
    events = paginator.get_page(page_number)

    context = {
        'events': events,
        'page_title': 'Upcoming Events',
        'page_subtitle': 'Discover exciting events and activities in the NORSU alumni community'
    }

    return render(request, 'landing/events.html', context)


def landing_announcements(request):
    """
    Display active announcements for unauthenticated users with pagination
    """
    announcements_list = Announcement.objects.filter(
        is_active=True
    ).order_by('-date_posted')

    paginator = Paginator(announcements_list, 10)  # Show 10 announcements per page
    page_number = request.GET.get('page')
    announcements = paginator.get_page(page_number)

    context = {
        'announcements': announcements,
        'page_title': 'Latest Announcements',
        'page_subtitle': 'Stay updated with the latest news and announcements from NORSU'
    }

    return render(request, 'landing/announcements.html', context)


def landing_news(request):
    """
    Display news content for unauthenticated users
    """
    # Get announcements categorized as news or high priority announcements
    try:
        from announcements.models import Category
        news_category = Category.objects.filter(name__icontains='news').first()
        if news_category:
            news_list = Announcement.objects.filter(
                is_active=True,
                category=news_category
            ).order_by('-date_posted')
        else:
            # Fallback to high priority announcements
            news_list = Announcement.objects.filter(
                is_active=True,
                priority_level__in=['HIGH', 'URGENT']
            ).order_by('-date_posted')
    except:
        news_list = Announcement.objects.filter(
            is_active=True,
            priority_level__in=['HIGH', 'URGENT']
        ).order_by('-date_posted')

    paginator = Paginator(news_list, 8)  # Show 8 news items per page
    page_number = request.GET.get('page')
    news = paginator.get_page(page_number)

    # Get featured news (first 3 items)
    featured_news = news_list[:3] if news_list else []

    context = {
        'news': news,
        'featured_news': featured_news,
        'page_title': 'Latest News',
        'page_subtitle': 'Stay informed with the latest news and updates from NORSU'
    }

    return render(request, 'landing/news.html', context)


def about_us(request):
    """
    Display About Us page with university information and statistics
    """
    # Get statistics
    try:
        alumni_count = Alumni.objects.filter(is_verified=True).count()
    except:
        alumni_count = 0

    try:
        group_count = AlumniGroup.objects.count()
    except:
        group_count = 0

    try:
        event_count = Event.objects.count()
    except:
        event_count = 0

    try:
        from jobs.models import Job
        job_count = Job.objects.count()
    except:
        job_count = 0

    # Sample staff information (this could be moved to a model later)
    staff_members = [
        {
            'name': 'Dr. Maria Santos',
            'position': 'Alumni Relations Director',
            'department': 'Office of Alumni Affairs',
            'email': 'maria.santos@norsu.edu.ph'
        },
        {
            'name': 'Prof. Juan Dela Cruz',
            'position': 'Alumni Engagement Coordinator',
            'department': 'Office of Alumni Affairs',
            'email': 'juan.delacruz@norsu.edu.ph'
        },
        {
            'name': 'Ms. Ana Rodriguez',
            'position': 'Alumni Database Manager',
            'department': 'Information Technology Services',
            'email': 'ana.rodriguez@norsu.edu.ph'
        }
    ]

    context = {
        'page_title': 'About NORSU Alumni Network',
        'page_subtitle': 'Learn more about our university, mission, and the people behind our alumni community',
        'alumni_count': alumni_count,
        'group_count': group_count,
        'event_count': event_count,
        'job_count': job_count,
        'staff_members': staff_members,
    }

    return render(request, 'landing/about_us.html', context)


def contact_us(request):
    """
    Display Contact Us page with contact form and information
    """
    from core.models.page_content import SiteConfiguration
    
    # Get site configuration for contact information
    site_config = SiteConfiguration.objects.first()
    
    context = {
        'page_title': 'Contact Us',
        'page_subtitle': 'Get in touch with the NORSU Alumni Network team',
        'site_config': site_config
    }

    return render(request, 'landing/contact_us.html', context)


@require_http_methods(["POST"])
def contact_us_submit(request):
    """
    Handle contact form submission
    """
    try:
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        # Basic validation
        if not all([name, email, subject, message]):
            messages.error(request, 'All fields are required.')
            return redirect('core:contact_us')
        
        # Send email logic would go here
        messages.success(request, 'Your message has been sent successfully!')
        return redirect('core:contact_us')
        
    except Exception as e:
        logger.error(f"Error processing contact form: {str(e)}")
        messages.error(request, 'There was an error processing your request. Please try again.')
        return redirect('core:contact_us')


# Superuser Creation Form
class SuperuserCreationForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username',
            'required': True
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter email address',
            'required': True
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password',
            'required': True
        }),
        min_length=8
    )
    
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password',
            'required': True
        }),
        min_length=8
    )
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError('A user with this username already exists.')
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('A user with this email already exists.')
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and confirm_password:
            if password != confirm_password:
                raise ValidationError('Passwords do not match.')
        
        return cleaned_data
    
    def save(self):
        """Create and return the superuser."""
        username = self.cleaned_data['username']
        email = self.cleaned_data['email']
        password = self.cleaned_data['password']
        
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        return user


# Superuser Creation View
@method_decorator([csrf_protect, never_cache], name='dispatch')
class SuperuserCreationView(View):
    template_name = 'core/create_superuser.html'
    form_class = SuperuserCreationForm
    
    def dispatch(self, request, *args, **kwargs):
        # Check if a superuser already exists
        if User.objects.filter(is_superuser=True).exists():
            # If superuser exists, make this page inaccessible
            raise Http404("Superuser creation is no longer available.")
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = self.form_class(request.POST)
        
        if form.is_valid():
            try:
                # Double-check that no superuser exists before creating
                if User.objects.filter(is_superuser=True).exists():
                    messages.error(request, 'A superuser already exists.')
                    raise Http404("Superuser creation is no longer available.")
                
                # Create the superuser
                user = form.save()
                
                messages.success(
                    request, 
                    f'Superuser "{user.username}" has been created successfully!'
                )
                
                # Redirect to homepage
                return redirect('/')
                
            except Exception as e:
                messages.error(
                    request, 
                    f'Error creating superuser: {str(e)}'
                )
        
        return render(request, self.template_name, {'form': form})

        # Send email (configure your email settings in settings.py)
        try:
            email_subject = f"Contact Form: {subject}"
            email_message = f"""
            Name: {name}
            Email: {email}
            Subject: {subject}

            Message:
            {message}
            """

            send_mail(
                email_subject,
                email_message,
                settings.DEFAULT_FROM_EMAIL,
                ['alumni@norsu.edu.ph'],  # Replace with actual email
                fail_silently=False,
            )

            messages.success(request, 'Thank you for your message! We will get back to you soon.')
            return redirect('core:contact_us')
        except Exception as e:
            logger.error(f"Error sending contact form email: {str(e)}")
            messages.error(request, 'There was an error sending your message. Please try again later.')
            return redirect('core:contact_us')