from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.http import HttpResponse
import logging
import time

logger = logging.getLogger(__name__)

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

# Import export utilities
from .export_utils import export_queryset, ModelExporter
from .export_utils import ExportMixin

@login_required
def admin_dashboard(request):
    """Main admin dashboard with comprehensive analytics"""
    from django.db import connection
    start_time = time.time()
    initial_query_count = len(connection.queries)
    
    # Log admin dashboard access
    logger.info(
        f"Admin dashboard accessed: User={request.user.username}",
        extra={
            'user_id': request.user.id,
            'is_staff': request.user.is_staff,
            'is_superuser': request.user.is_superuser,
            'ip_address': request.META.get('REMOTE_ADDR'),
            'action': 'admin_dashboard_access'
        }
    )
    
    # Check if user is staff or admin
    if not request.user.is_staff and not request.user.is_superuser:
        logger.warning(
            f"Unauthorized admin dashboard access attempt: User={request.user.username}",
            extra={
                'user_id': request.user.id,
                'ip_address': request.META.get('REMOTE_ADDR'),
                'action': 'unauthorized_access'
            }
        )
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
    
    # Announcement Statistics
    total_announcements = Announcement.objects.count()
    
    
    # Alumni by College Data
    alumni_by_college = Alumni.objects.values('college').annotate(
        count=Count('id')
    ).order_by('-count')

    # Format college data for template
    formatted_college_data = []
    college_choices_dict = dict(Alumni.COLLEGE_CHOICES)

    for item in alumni_by_college:
        college_code = item['college']
        college_name = college_choices_dict.get(college_code, college_code)
        formatted_college_data.append({
            'college_code': college_code,
            'college_name': college_name,
            'count': item['count']
        })

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
        
        # Announcement stats
        'total_announcements': total_announcements,
        
        
        # Recent activity
        'recent_users': recent_users,
        'recent_donations': recent_donations,
        'recent_events': recent_events,

        # Alumni by college data
        'alumni_by_college': formatted_college_data,
    }
    
    # Calculate performance metrics
    elapsed_time = time.time() - start_time
    final_query_count = len(connection.queries)
    queries_executed = final_query_count - initial_query_count
    
    # Log performance metrics
    logger.debug(
        f"Admin dashboard context built: Time={elapsed_time:.3f}s, Queries={queries_executed}",
        extra={
            'user_id': request.user.id,
            'elapsed_time': elapsed_time,
            'queries_executed': queries_executed,
            'action': 'admin_dashboard_complete'
        }
    )
    
    # Log slow operations warning
    if elapsed_time > 3.0:
        logger.warning(
            f"Slow admin dashboard: Time={elapsed_time:.3f}s, Queries={queries_executed}",
            extra={
                'user_id': request.user.id,
                'elapsed_time': elapsed_time,
                'queries_executed': queries_executed,
                'threshold': 3.0,
                'action': 'slow_operation'
            }
        )
    
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

@login_required
def alumni_by_college_api(request):
    """API endpoint for alumni count by college data"""
    # Check permissions
    if not request.user.is_staff and not request.user.is_superuser:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    try:
        # Get alumni count by college
        college_data = Alumni.objects.values('college').annotate(
            count=Count('id')
        ).order_by('-count')

        # Format the data with college display names
        formatted_data = []
        college_choices_dict = dict(Alumni.COLLEGE_CHOICES)

        for item in college_data:
            college_code = item['college']
            college_name = college_choices_dict.get(college_code, college_code)
            formatted_data.append({
                'college_code': college_code,
                'college_name': college_name,
                'count': item['count']
            })

        # Handle case where there might be alumni with no college (though unlikely given model constraints)
        # This is for defensive programming
        total_alumni = Alumni.objects.count()
        counted_alumni = sum(item['count'] for item in formatted_data)

        if total_alumni > counted_alumni:
            formatted_data.append({
                'college_code': 'UNKNOWN',
                'college_name': 'Unknown College',
                'count': total_alumni - counted_alumni
            })

        return JsonResponse({
            'success': True,
            'data': formatted_data,
            'total_alumni': total_alumni
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# Export Views
@login_required
def export_alumni(request, format_type='csv'):
    """Export alumni data in specified format"""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('core:home')
    
    queryset = Alumni.objects.select_related('user').all()
    export_config = ModelExporter.get_alumni_export_config()
    
    return export_queryset(queryset, format_type, 'alumni', export_config)

@login_required
def export_jobs(request, format_type='csv'):
    """Export jobs data in specified format"""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('core:home')
    
    queryset = JobPosting.objects.all()
    export_config = ModelExporter.get_job_export_config()
    
    return export_queryset(queryset, format_type, 'jobs', export_config)

@login_required
def export_mentorships(request, format_type='csv'):
    """Export mentorships data in specified format"""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('core:home')
    
    queryset = MentorshipRequest.objects.select_related('mentor__user', 'mentee__user').all()
    export_config = ModelExporter.get_mentorship_export_config()
    
    return export_queryset(queryset, format_type, 'mentorships', export_config)

@login_required
def export_events(request, format_type='csv'):
    """Export events data in specified format"""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('core:home')
    
    queryset = Event.objects.all()
    export_config = ModelExporter.get_event_export_config()
    
    return export_queryset(queryset, format_type, 'events', export_config)

@login_required
def export_donations(request, format_type='csv'):
    """Export donations data in specified format"""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('core:home')
    
    queryset = Donation.objects.select_related('donor__user', 'campaign').all()
    export_config = ModelExporter.get_donation_export_config()
    
    return export_queryset(queryset, format_type, 'donations', export_config)

@login_required
def export_users(request, format_type='csv'):
    """Export users data in specified format"""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('core:home')
    
    queryset = User.objects.all()
    export_config = ModelExporter.get_user_export_config()
    
    return export_queryset(queryset, format_type, 'users', export_config)

@login_required
def export_announcements(request, format_type='csv'):
    """Export announcements data in specified format"""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('core:home')
    
    queryset = Announcement.objects.select_related('category', 'author').all()
    export_config = ModelExporter.get_announcement_export_config()
    
    return export_queryset(queryset, format_type, 'announcements', export_config)

@login_required
def export_feedback(request, format_type='csv'):
    """Export feedback data in specified format"""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('core:home')
    
    queryset = Feedback.objects.select_related('user').all()
    export_config = ModelExporter.get_feedback_export_config()
    
    return export_queryset(queryset, format_type, 'feedback', export_config)

@login_required
def export_surveys(request, format_type='csv'):
    """Export surveys data in specified format"""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('core:home')
    
    queryset = Survey.objects.select_related('created_by').all()
    export_config = ModelExporter.get_survey_export_config()
    
    # Log export operation
    logger.info(
        f"Survey export requested: Format={format_type}, Count={queryset.count()}",
        extra={
            'format_type': format_type,
            'record_count': queryset.count(),
            'user_id': request.user.id,
            'action': 'data_export'
        }
    )
    
    return export_queryset(queryset, format_type, 'surveys', export_config)

@login_required
def export_all_data(request, format_type='csv'):
    """Export all data in specified format"""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('core:home')
    
    # This would need to be implemented as a more complex export
    # For now, redirect to dashboard
    messages.info(request, _('Bulk export functionality coming soon.'))
    return redirect('core:admin_dashboard')

@login_required
def bulk_export_interface(request):
    """Bulk export interface for selecting multiple models to export"""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('core:home')
    
    # Get counts for each model
    context = {
        'total_alumni': Alumni.objects.count(),
        'total_users': User.objects.count(),
        'total_jobs': JobPosting.objects.count(),
        'total_mentorships': MentorshipRequest.objects.count(),
        'total_events': Event.objects.count(),
        'total_donations': Donation.objects.count(),
        'total_announcements': Announcement.objects.count(),
        'total_feedback': Feedback.objects.count(),
        'total_surveys': Survey.objects.count(),
    }
    
    return render(request, 'admin/bulk_export.html', context)

@login_required
def bulk_export_process(request):
    """Process bulk export request"""
    if not request.user.is_staff and not request.user.is_superuser:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('core:home')
    
    if request.method == 'POST':
        selected_models = request.POST.getlist('models')
        format_type = request.POST.get('format_type', 'csv')
        
        # Log bulk export start
        logger.info(
            f"Bulk export started: Models={selected_models}, Format={format_type}",
            extra={
                'selected_models': selected_models,
                'model_count': len(selected_models),
                'format_type': format_type,
                'user_id': request.user.id,
                'action': 'bulk_export_start'
            }
        )
        
        if not selected_models:
            messages.error(request, _('Please select at least one model to export.'))
            return redirect('core:bulk_export_interface')
        
        # Create a zip file containing all selected exports
        import zipfile
        import tempfile
        from django.core.files.base import ContentFile
        
        exported_count = 0
        failed_count = 0
        failed_models = []
        
        # Create temporary file for zip
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
            with zipfile.ZipFile(tmp_file.name, 'w') as zip_file:
                
                for model_name in selected_models:
                    try:
                        # Get the appropriate queryset and config based on model
                        if model_name == 'alumni':
                            queryset = Alumni.objects.select_related('user').all()
                            export_config = ModelExporter.get_alumni_export_config()
                        elif model_name == 'users':
                            queryset = User.objects.all()
                            export_config = ModelExporter.get_user_export_config()
                        elif model_name == 'jobs':
                            queryset = JobPosting.objects.all()
                            export_config = ModelExporter.get_job_export_config()
                        elif model_name == 'mentorships':
                            queryset = MentorshipRequest.objects.select_related('mentor__user', 'mentee__user').all()
                            export_config = ModelExporter.get_mentorship_export_config()
                        elif model_name == 'events':
                            queryset = Event.objects.all()
                            export_config = ModelExporter.get_event_export_config()
                        elif model_name == 'donations':
                            queryset = Donation.objects.select_related('donor__user', 'campaign').all()
                            export_config = ModelExporter.get_donation_export_config()
                        elif model_name == 'announcements':
                            queryset = Announcement.objects.select_related('category', 'author').all()
                            export_config = ModelExporter.get_announcement_export_config()
                        elif model_name == 'feedback':
                            queryset = Feedback.objects.select_related('user').all()
                            export_config = ModelExporter.get_feedback_export_config()
                        elif model_name == 'surveys':
                            queryset = Survey.objects.select_related('created_by').all()
                            export_config = ModelExporter.get_survey_export_config()
                        else:
                            continue
                        
                        # Generate the export
                        if format_type == 'csv':
                            response = ExportMixin().export_csv(
                                queryset, 
                                f"{model_name}_export", 
                                export_config.get('field_names'),
                                export_config.get('field_labels')
                            )
                            filename = f"{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                        elif format_type == 'excel':
                            response = ExportMixin().export_excel(
                                queryset, 
                                f"{model_name}_export", 
                                export_config.get('field_names'),
                                export_config.get('field_labels'),
                                export_config.get('sheet_name', 'Data')
                            )
                            filename = f"{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                        elif format_type == 'pdf':
                            response = ExportMixin().export_pdf(
                                queryset, 
                                f"{model_name}_export", 
                                export_config.get('field_names'),
                                export_config.get('field_labels'),
                                export_config.get('sheet_name', 'Data Export')
                            )
                            filename = f"{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                        else:
                            continue
                        
                        # Add file to zip
                        zip_file.writestr(filename, response.content)
                        exported_count += 1
                        
                        logger.info(
                            f"Model exported successfully: Model={model_name}, Format={format_type}",
                            extra={
                                'model_name': model_name,
                                'format_type': format_type,
                                'user_id': request.user.id,
                                'action': 'model_export_success'
                            }
                        )
                        
                    except Exception as e:
                        # Log error but continue with other models
                        failed_count += 1
                        failed_models.append(model_name)
                        logger.error(
                            f"Error exporting model: Model={model_name}, Format={format_type}, Error={str(e)}",
                            extra={
                                'model_name': model_name,
                                'format_type': format_type,
                                'user_id': request.user.id,
                                'error_type': type(e).__name__,
                                'exc_info': True,
                                'action': 'model_export_failed'
                            }
                        )
                        continue
                
                # Add a README file to the zip
                readme_content = f"""Bulk Export Report
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Format: {format_type.upper()}
Models exported: {', '.join(selected_models)}
Total files: {len(selected_models)}

This zip file contains exported data from the following models:
{chr(10).join([f"- {model}" for model in selected_models])}

Each file is named with the model name and timestamp for easy identification.
"""
                zip_file.writestr('README.txt', readme_content)
        
        # Read the zip file and create response
        with open(tmp_file.name, 'rb') as f:
            zip_content = f.read()
        
        # Clean up temporary file
        import os
        os.unlink(tmp_file.name)
        
        # Log bulk export completion
        logger.info(
            f"Bulk export completed: Exported={exported_count}, Failed={failed_count}, Format={format_type}",
            extra={
                'exported_count': exported_count,
                'failed_count': failed_count,
                'failed_models': failed_models,
                'format_type': format_type,
                'total_models': len(selected_models),
                'user_id': request.user.id,
                'action': 'bulk_export_complete'
            }
        )
        
        # Create response
        response = HttpResponse(zip_content, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="bulk_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip"'
        
        return response
    
    return redirect('core:bulk_export_interface')
