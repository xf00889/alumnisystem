from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.core.cache import cache
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from .models import JobPosting, JobApplication, RequiredDocument, ScrapedJob
from .forms import JobPostingForm, JobApplicationForm, RequiredDocumentFormSet
from .scraper_forms import JobScraperForm
from .scraper_utils import scraper

# Initialize multi-source scraper manager - ensure it's always defined
scraper_manager = None
try:
    from .scraper_manager import JobScraperManager
    scraper_manager = JobScraperManager()
except (ImportError, Exception) as e:
    scraper_manager = None
    import logging
    logger_views = logging.getLogger(__name__)
    logger_views.warning(f"JobScraperManager not available: {str(e)}")
from .utils import calculate_job_match_score, get_skill_recommendations
from accounts.models import Profile, SkillMatch
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side
import logging
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)

def is_hr_or_admin(user):
    """Check if user is HR or admin"""
    return user.is_superuser or user.groups.filter(name='HR').exists()

def careers(request):
    """Public careers page for job listings"""
    jobs = JobPosting.objects.filter(is_active=True).order_by('-posted_date')
    
    # Get filter parameters (for future implementation)
    job_type = request.GET.get('job_type')
    location = request.GET.get('location')
    category = request.GET.get('category')
    search_query = request.GET.get('q')
    
    # Apply filters (prepared for future implementation)
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    if location:
        jobs = jobs.filter(location__icontains=location)
    if category:
        jobs = jobs.filter(category=category)
    if search_query:
        jobs = jobs.filter(
            Q(job_title__icontains=search_query) |
            Q(company_name__icontains=search_query) |
            Q(job_description__icontains=search_query)
        )
    
    # Get featured jobs
    featured_jobs = jobs.filter(is_featured=True)[:3]
    
    # Get recent jobs (excluding featured ones)
    recent_jobs = jobs.exclude(is_featured=True)[:10]
    
    # Get job statistics
    stats = {
        'total_jobs': jobs.count(),
        'featured_jobs': featured_jobs.count(),
        'recent_jobs': recent_jobs.count(),
    }
    
    # Prepare filter options for future use
    filter_options = {
        'job_types': JobPosting.JOB_TYPE_CHOICES,
        'categories': JobPosting.CATEGORY_CHOICES,
        'locations': JobPosting.objects.filter(is_active=True).values_list('location', flat=True).distinct().order_by('location'),
    }
    
    context = {
        'featured_jobs': featured_jobs,
        'recent_jobs': recent_jobs,
        'stats': stats,
        'filter_options': filter_options,
        'current_filters': {
            'job_type': job_type,
            'location': location,
            'category': category,
            'search_query': search_query,
        },
        'page_title': 'Career Opportunities - NORSU Alumni',
        'page_description': 'Discover exciting career opportunities and job postings from NORSU alumni network. Find your next career move with our exclusive job board.',
    }
    return render(request, 'jobs/careers.html', context)

def get_job_details(request, job_id):
    """Get job details as JSON for modal display"""
    try:
        job = get_object_or_404(JobPosting, id=job_id, is_active=True)
        
        # Prepare job data for JSON response
        job_data = {
            'id': job.id,
            'job_title': job.job_title,
            'company_name': job.company_name,
            'location': job.location,
            'job_type': job.get_job_type_display(),
            'job_description': job.job_description,
            'requirements': job.requirements,
            'responsibilities': job.responsibilities,
            'experience_level': job.get_experience_level_display(),
            'skills_required': job.skills_required,
            'education_requirements': job.education_requirements,
            'benefits': job.benefits,
            'salary_range': job.salary_range,
            'application_link': job.application_link,
            'posted_date': job.posted_date.strftime('%B %d, %Y'),
            'is_featured': job.is_featured,
            'category': job.get_category_display(),
            'source_type': job.source_type,
            'source_type_display': job.get_source_type_display(),
            'accepts_internal_applications': job.accepts_internal_applications,
        }
        
        return JsonResponse({
            'success': True,
            'job': job_data,
            'user': {
                'is_authenticated': request.user.is_authenticated,
                'is_alumni': request.user.is_authenticated,  # For now, assume authenticated users are alumni
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting job details: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Failed to load job details'
        }, status=500)

def check_job_application_eligibility(request, job_id):
    """Check if user can apply for a specific job based on source_type restrictions"""
    try:
        job = get_object_or_404(JobPosting, id=job_id, is_active=True)
        
        # Check source_type restrictions
        if job.source_type == 'INTERNAL':
            if not request.user.is_authenticated:
                return JsonResponse({
                    'success': False,
                    'eligible': False,
                    'message': 'Please log in or register to apply for this job.',
                    'redirect_url': '/accounts/login/'
                })
        
        return JsonResponse({
            'success': True,
            'eligible': True,
            'message': 'You are eligible to apply for this job.'
        })
        
    except Exception as e:
        logger.error(f"Error checking job application eligibility: {str(e)}")
        return JsonResponse({
            'success': False,
            'eligible': False,
            'message': 'Unable to check application eligibility.'
        }, status=500)

def job_list(request):
    jobs = JobPosting.objects.filter(is_active=True)
    
    # Get scraped jobs
    scraped_jobs = ScrapedJob.objects.filter(is_active=True).order_by('-scraped_at')
    
    # Check if user wants to view scraped jobs
    view_type = request.GET.get('view_type', 'posted')  # 'posted' or 'scraped'
    
    # Search functionality
    query = request.GET.get('q')
    if query:
        if view_type == 'scraped':
            scraped_jobs = scraped_jobs.filter(
                Q(search_keyword__icontains=query) |
                Q(search_location__icontains=query)
            )
        else:
            jobs = jobs.filter(
                Q(job_title__icontains=query) |
                Q(company_name__icontains=query) |
                Q(location__icontains=query) |
                Q(job_description__icontains=query)
            )
    
    # Filtering
    job_type = request.GET.get('job_type')
    source_type = request.GET.get('source_type')
    
    if job_type and view_type == 'posted':
        jobs = jobs.filter(job_type=job_type)
    if source_type:
        if view_type == 'scraped':
            scraped_jobs = scraped_jobs.filter(source=source_type)
        else:
            jobs = jobs.filter(source_type=source_type)
    
    # Skill-based view toggle (only for posted jobs)
    skill_based_view = request.GET.get('skill_based', 'false').lower() == 'true'
    
    # Get user profile if authenticated and skill-based view is enabled
    user_profile = None
    job_matches = []
    recommended_skills = []
    
    if request.user.is_authenticated and skill_based_view and view_type == 'posted':
        try:
            user_profile = Profile.objects.get(user=request.user)
            
            # Get job matches from database
            skill_matches = SkillMatch.objects.filter(
                profile=user_profile, 
                job__in=jobs
            ).select_related('job')
            
            # If no matches exist yet or all are outdated, calculate them on the fly
            if not skill_matches.exists():
                for job in jobs:
                    score, matched_skills, missing_skills = calculate_job_match_score(
                        user_profile, job, required_skills_only=False
                    )
                    if score > 0:
                        job_matches.append({
                            'job': job,
                            'score': score,
                            'matched_skills': matched_skills,
                            'missing_skills': missing_skills
                        })
                
                # Sort by score descending
                job_matches.sort(key=lambda x: x['score'], reverse=True)
            else:
                # Convert existing matches to the expected format
                for match in skill_matches:
                    job_matches.append({
                        'job': match.job,
                        'score': match.match_score,
                        'matched_skills': json.loads(match.matched_skills) if match.matched_skills else {},
                        'missing_skills': json.loads(match.missing_skills) if match.missing_skills else {}
                    })
            
            # Sort by score descending
            job_matches.sort(key=lambda x: x['score'], reverse=True)
            
            # Get skill recommendations
            recommended_skills = get_skill_recommendations(user_profile)
        except Profile.DoesNotExist:
            pass
        
    # Sorting
    sort = request.GET.get('sort')
    if skill_based_view and job_matches and view_type == 'posted':
        # Already sorted by match score above
        pass
    elif sort == 'oldest':
        jobs = jobs.order_by('posted_date')
    else:  # newest first is default
        jobs = jobs.order_by('-posted_date')
    
    # Featured jobs
    featured_jobs = jobs.filter(is_featured=True)[:5]
    
    # For skill-based view, use the job_matches list
    if skill_based_view and user_profile and view_type == 'posted':
        paginator = Paginator([match['job'] for match in job_matches], 10)
        page = request.GET.get('page')
        jobs_page = paginator.get_page(page)
        
        # Create a map for easy lookup of match data
        match_data = {match['job'].id: match for match in job_matches}
    elif view_type == 'scraped':
        # Pagination for scraped jobs
        paginator = Paginator(scraped_jobs, 10)
        page = request.GET.get('page')
        jobs_page = paginator.get_page(page)
        match_data = {}
    else:
        # Pagination for regular view
        paginator = Paginator(jobs, 10)
        page = request.GET.get('page')
        jobs_page = paginator.get_page(page)
        match_data = {}
    
    # Get scraped source choices
    scraped_source_choices = getattr(ScrapedJob, 'SOURCE_CHOICES', [])
    
    context = {
        'jobs': jobs_page,
        'featured_jobs': featured_jobs,
        'current_query': query,
        'current_job_type': job_type,
        'current_source_type': source_type,
        'current_sort': sort,
        'job_types': JobPosting.JOB_TYPE_CHOICES,
        'source_types': JobPosting.SOURCE_TYPE_CHOICES,
        'scraped_source_choices': scraped_source_choices,
        'skill_based_view': skill_based_view,
        'match_data': match_data,
        'recommended_skills': recommended_skills[:5] if recommended_skills else [],  # Show top 5 recommendations
        'view_type': view_type,
        'scraped_jobs': scraped_jobs if view_type == 'scraped' else None,
    }
    return render(request, 'jobs/job_list.html', context)

def job_detail(request, slug):
    job = get_object_or_404(JobPosting, slug=slug)
    user_application = None
    applicants = None
    
    if request.user.is_authenticated:
        user_application = JobApplication.objects.filter(job=job, applicant=request.user).first()
        
        # Add applicants list for admin/HR users
        if request.user.is_staff or is_hr_or_admin(request.user):
            applicants = job.applications.all().select_related('applicant__profile')
    
    context = {
        'job': job,
        'user_application': user_application,
        'applicants': applicants,
    }
    return render(request, 'jobs/job_detail.html', context)

@login_required
@user_passes_test(is_hr_or_admin)
def manage_jobs(request):
    jobs = JobPosting.objects.all()
    
    # Get statistics
    stats = {
        'active_jobs': jobs.filter(is_active=True).count(),
        'internal_jobs': jobs.filter(source_type='INTERNAL').count(),
        'total_applications': JobApplication.objects.count(),
        'pending_applications': JobApplication.objects.filter(status='PENDING').count(),
    }
    
    # Pagination
    paginator = Paginator(jobs, 10)
    page = request.GET.get('page')
    jobs = paginator.get_page(page)
    
    context = {
        'jobs': jobs,
        'stats': stats,
    }
    return render(request, 'jobs/manage_jobs.html', context)

@login_required
@user_passes_test(is_hr_or_admin)
def post_job(request):
    if request.method == 'POST':
        form = JobPostingForm(request.POST)
        document_formset = RequiredDocumentFormSet(request.POST)
        
        if form.is_valid() and document_formset.is_valid():
            try:
                with transaction.atomic():
                    # Save the job posting
                    job = form.save(commit=False)
                    job.posted_by = request.user
                    job.source = 'manual'
                    job.save()
                    
                    # Save document requirements for internal jobs
                    if job.source_type == 'INTERNAL':
                        document_formset.instance = job
                        document_formset.save()
                    
                    messages.success(request, 'Job posting created successfully!')
                    return redirect('jobs:job_detail', slug=job.slug)
            except Exception as e:
                messages.error(request, f'Error creating job posting: {str(e)}')
        else:
            # Add form errors to messages
            if form.errors:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
            if document_formset.errors:
                for form_errors in document_formset.errors:
                    for field, errors in form_errors.items():
                        for error in errors:
                            messages.error(request, f'Document requirement - {field}: {error}')
            if document_formset.non_form_errors():
                for error in document_formset.non_form_errors():
                    messages.error(request, f'Document requirements: {error}')
    else:
        form = JobPostingForm(initial={'is_active': True})  # Set is_active to True by default
        document_formset = RequiredDocumentFormSet()
    
    return render(request, 'jobs/post_job.html', {
        'form': form,
        'document_formset': document_formset
    })

@login_required
@user_passes_test(is_hr_or_admin)
def edit_job(request, slug):
    job = get_object_or_404(JobPosting, slug=slug)
    if request.method == 'POST':
        form = JobPostingForm(request.POST, instance=job)
        document_formset = RequiredDocumentFormSet(request.POST, instance=job)
        
        if form.is_valid() and document_formset.is_valid():
            try:
                with transaction.atomic():
                    job = form.save()
                    
                    if job.source_type == 'INTERNAL':
                        document_formset.save()
                    else:
                        # Remove all document requirements for external jobs
                        job.required_documents.all().delete()
                    
                    messages.success(request, 'Job posting updated successfully!')
                    return redirect('jobs:job_detail', slug=job.slug)
            except Exception as e:
                messages.error(request, f'Error updating job posting: {str(e)}')
    else:
        form = JobPostingForm(instance=job)
        document_formset = RequiredDocumentFormSet(instance=job)
    
    return render(request, 'jobs/post_job.html', {
        'form': form,
        'document_formset': document_formset,
        'job': job
    })

@login_required
@user_passes_test(is_hr_or_admin)
def delete_job(request, slug):
    job = get_object_or_404(JobPosting, slug=slug)
    if request.method == 'POST':
        job.delete()
        messages.success(request, 'Job posting deleted successfully!')
        return redirect('jobs:manage_jobs')
    return redirect('jobs:job_detail', slug=slug)

@login_required
def apply_for_job(request, slug):
    job = get_object_or_404(JobPosting, slug=slug, is_active=True)
    
    # Check if user has already applied
    if JobApplication.objects.filter(job=job, applicant=request.user).exists():
        messages.warning(request, 'You have already applied for this position.')
        return redirect('jobs:job_detail', slug=slug)
    
    # For internal jobs, show the application form
    if job.source_type == 'INTERNAL' or job.accepts_internal_applications:
        if request.method == 'POST':
            form = JobApplicationForm(request.POST, request.FILES, job=job)
            if form.is_valid():
                try:
                    with transaction.atomic():
                        application = form.save(commit=False)
                        application.job = job
                        application.applicant = request.user
                        application.save()
                        
                        # Handle required documents
                        for doc in job.required_documents.filter(is_required=True):
                            field_name = f'document_{doc.id}'
                            if field_name in request.FILES:
                                document = request.FILES[field_name]
                                # Store the document with the application
                                # You might want to create a separate model for this
                                # For now, we'll store it in additional_documents
                                application.additional_documents = document
                                application.save()
                        
                        messages.success(request, 'Your application has been submitted successfully!')
                        return redirect('jobs:job_detail', slug=slug)
                except Exception as e:
                    messages.error(request, f'Error submitting application: {str(e)}')
        else:
            form = JobApplicationForm(job=job)
        
        context = {
            'form': form,
            'job': job,
        }
        return render(request, 'jobs/apply.html', context)
    
    # For external jobs with application link, redirect to external site
    elif job.application_link:
        return redirect(job.application_link)
    
    # For external jobs without application link, redirect back with message
    else:
        messages.info(request, 'Please contact the organization directly to apply for this position.')
        return redirect('jobs:job_detail', slug=slug)

@login_required
@user_passes_test(is_hr_or_admin)
def manage_applications(request, slug):
    job = get_object_or_404(JobPosting, slug=slug)
    applications = job.applications.all()
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        applications = applications.filter(status=status)
    
    # Get application statistics
    stats = {
        'pending': applications.filter(status='PENDING').count(),
        'shortlisted': applications.filter(status='SHORTLISTED').count(),
        'interviewed': applications.filter(status='INTERVIEWED').count(),
        'accepted': applications.filter(status='ACCEPTED').count(),
    }
    
    # Pagination
    paginator = Paginator(applications, 20)
    page = request.GET.get('page')
    applications = paginator.get_page(page)
    
    context = {
        'job': job,
        'applications': applications,
        'stats': stats,
        'status': status,
        'status_choices': JobApplication.STATUS_CHOICES,
    }
    return render(request, 'jobs/manage_applications.html', context)

@login_required
@user_passes_test(is_hr_or_admin)
def update_application_status(request, application_id):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        application = get_object_or_404(JobApplication, id=application_id)
        data = json.loads(request.body)
        status = data.get('status')
        
        if status in dict(JobApplication.STATUS_CHOICES):
            application.status = status
            application.save()
            return JsonResponse({'success': True})
    
    return JsonResponse({'success': False}, status=400)

@login_required
@user_passes_test(is_hr_or_admin)
def application_details(request, application_id):
    application = get_object_or_404(JobApplication, id=application_id)
    context = {
        'application': application,
        'status_choices': JobApplication.STATUS_CHOICES,
    }
    html = render_to_string('jobs/application_details.html', context)
    return JsonResponse({'html': html})

@login_required
@user_passes_test(is_hr_or_admin)
def add_application_note(request, application_id):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        application = get_object_or_404(JobApplication, id=application_id)
        data = json.loads(request.body)
        note = data.get('note')
        
        if note:
            current_notes = application.notes or ''
            timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
            new_note = f"[{timestamp}] {request.user.get_full_name()}: {note}\n"
            application.notes = new_note + current_notes
            application.save()
            return JsonResponse({'success': True})
    
    return JsonResponse({'success': False}, status=400)

@login_required
@user_passes_test(is_hr_or_admin)
def send_application_email(request, application_id):
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': False,
            'error': 'Invalid request'
        }, status=400)

    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Invalid method'
        }, status=405)

    try:
        application = get_object_or_404(JobApplication, id=application_id)
        data = json.loads(request.body)
        subject = data.get('subject')
        message = data.get('message')
        
        if not subject or not message:
            return JsonResponse({
                'success': False,
                'error': 'Subject and message are required.'
            }, status=400)
        
        # Send email using unified email system
        try:
            from core.email_utils import send_email_with_provider
            
            success = send_email_with_provider(
                subject=subject,
                message=message,
                recipient_list=[application.applicant.email],
                from_email=settings.DEFAULT_FROM_EMAIL,
                fail_silently=False
            )
            
            if not success:
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to send email'
                }, status=500)
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Failed to send email: {str(e)}'
            }, status=500)
        
        # Log the email in notes
        timestamp = timezone.now().strftime('%Y-%m-%d %H:%M')
        note = f"[{timestamp}] Email sent by {request.user.get_full_name()}\nSubject: {subject}\nMessage: {message}\n\n"
        
        if application.notes:
            application.notes = note + application.notes
        else:
            application.notes = note
        
        application.save()
        
        return JsonResponse({'success': True})
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@user_passes_test(is_hr_or_admin)
def export_applicants(request, job_id):
    """Export job applicants to Excel file"""
    job = get_object_or_404(JobPosting, id=job_id)
    applicants = job.applications.all().select_related('applicant')
    
    # Create a workbook and add a worksheet
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename=Applicants-{job.slug}-{timezone.now().strftime("%Y%m%d")}.xlsx'
    
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = 'Applicants'
    
    # Define the column headers
    columns = [
        'ID', 'Name', 'Email', 'Application Date', 'Status', 
        'Phone', 'Location', 'Skills', 'Experience', 'Notes'
    ]
    
    # Write the headers to the worksheet
    for col_num, column_title in enumerate(columns, 1):
        cell = worksheet.cell(row=1, column=col_num)
        cell.value = column_title
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color='FFCCCCCC', end_color='FFCCCCCC', fill_type='solid')
        cell.border = Border(
            left=Side(border_style='thin', color='FF000000'),
            right=Side(border_style='thin', color='FF000000'),
            top=Side(border_style='thin', color='FF000000'),
            bottom=Side(border_style='thin', color='FF000000')
        )
    
    # Write the data to the worksheet
    row_num = 2
    for application in applicants:
        user = application.applicant
        
        # Get profile data if available
        try:
            profile = user.profile
            phone = profile.phone_number if hasattr(profile, 'phone_number') else 'N/A'
            location = profile.location if hasattr(profile, 'location') else 'N/A'
            skills = ", ".join([skill.name for skill in profile.skills.all()]) if hasattr(profile, 'skills') else 'N/A'
            experience = profile.years_of_experience if hasattr(profile, 'years_of_experience') else 'N/A'
        except:
            phone = location = skills = experience = 'N/A'
        
        row = [
            application.id,
            user.get_full_name(),
            user.email,
            application.application_date.strftime('%Y-%m-%d'),
            application.get_status_display(),
            phone,
            location,
            skills,
            experience,
            application.notes or 'N/A'
        ]
        
        for col_num, cell_value in enumerate(row, 1):
            cell = worksheet.cell(row=row_num, column=col_num)
            cell.value = cell_value
            
        row_num += 1
    
    # Auto-adjust column widths
    for column in worksheet.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        adjusted_width = (max_length + 2)
        worksheet.column_dimensions[column_letter].width = adjusted_width
    
    workbook.save(response)
    return response



@login_required
@user_passes_test(is_hr_or_admin)
def bulk_update_jobs(request):
    """Admin function to perform bulk operations on job postings"""
    if request.method == 'POST':
        action = request.POST.get('action')
        job_ids = request.POST.getlist('job_ids')
        
        if not job_ids:
            messages.error(request, 'No jobs selected for bulk operation.')
            return redirect('jobs:manage_jobs')
        
        jobs = JobPosting.objects.filter(id__in=job_ids)
        
        try:
            if action == 'activate':
                jobs.update(is_active=True)
                messages.success(request, f'Successfully activated {jobs.count()} job postings.')
            elif action == 'deactivate':
                jobs.update(is_active=False)
                messages.success(request, f'Successfully deactivated {jobs.count()} job postings.')
            elif action == 'feature':
                jobs.update(is_featured=True)
                messages.success(request, f'Successfully featured {jobs.count()} job postings.')
            elif action == 'unfeature':
                jobs.update(is_featured=False)
                messages.success(request, f'Successfully unfeatured {jobs.count()} job postings.')
            elif action == 'delete':
                count = jobs.count()
                jobs.delete()
                messages.success(request, f'Successfully deleted {count} job postings.')
            else:
                messages.error(request, 'Invalid bulk action selected.')
        except Exception as e:
            messages.error(request, f'Error performing bulk operation: {str(e)}')
            logger.exception('Error in bulk update jobs')
        
        return redirect('jobs:manage_jobs')
    
    # GET request - redirect to manage jobs
    return redirect('jobs:manage_jobs')


@login_required
def job_scraper(request):
    """Job scraper main page with form"""
    # Get available sources for the form
    available_sources = [('BOSSJOB', 'BossJob.ph')]  # Default
    if scraper_manager:
        available_sources = [(s, scraper_manager._get_source_display_name(s)) for s in scraper_manager.get_available_sources()]
    
    form = JobScraperForm(available_sources=available_sources)
    return render(request, 'jobs/job_scraper.html', {
        'form': form,
        'page_title': 'Job Scraper - Find Jobs from Multiple Sources'
    })


@login_required
def job_scraper_results(request):
    """HTMX endpoint for job scraper results"""
    if request.method == 'POST':
        form = JobScraperForm(request.POST)
        
        if form.is_valid():
            keyword = form.cleaned_data['keyword']
            location = form.cleaned_data['location']
            
            try:
                # Get selected sources from form
                sources = form.cleaned_data.get('sources', []) or request.POST.getlist('sources', [])
                
                # Perform the scraping - try multi-source manager first, fallback to single source
                
                if scraper_manager and sources:
                    # Use multi-source scraper
                    logger.info(f"Using multi-source scraper for sources: {sources}")
                    results = scraper_manager.search_jobs(keyword, location, sources=sources, use_cache=False)
                elif scraper_manager:
                    # Use multi-source scraper with all available sources
                    logger.info(f"Using multi-source scraper for all available sources")
                    results = scraper_manager.search_jobs(keyword, location, use_cache=False)
                else:
                    # Fallback to single source (BossJob only)
                    logger.info(f"Using single-source scraper (BossJob.ph)")
                    results = scraper.search_jobs(keyword, location)
                
                # Log the scraping activity
                logger.info(f"User {request.user.username} scraped jobs for '{keyword}' in '{location}' - Found {results.get('total_found', 0)} jobs")
                
                # Save scraped data as JSON file
                try:
                    # Create directory if it doesn't exist
                    json_dir = os.path.join(settings.MEDIA_ROOT, 'scraped_jobs')
                    os.makedirs(json_dir, exist_ok=True)
                    
                    # Create filename with timestamp
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"scraped_jobs_{keyword.replace(' ', '_')}_{location.replace(' ', '_')}_{timestamp}.json"
                    filepath = os.path.join(json_dir, filename)
                    
                    # Prepare data for JSON export
                    export_data = {
                        'search_params': {
                            'keyword': keyword,
                            'location': location,
                            'scraped_by': request.user.username,
                            'scraped_at': datetime.now().isoformat()
                        },
                        'results': results
                    }
                    
                    # Write JSON file
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(export_data, f, indent=2, ensure_ascii=False)
                    
                    logger.info(f"Scraped data saved to: {filepath}")
                    
                except Exception as e:
                    logger.error(f"Error saving scraped data to JSON: {str(e)}")
                
                # Save to database - deactivate old entries for same search
                try:
                    # Deactivate previous scraped jobs for the same keyword/location/user combination
                    ScrapedJob.objects.filter(
                        search_keyword=keyword,
                        search_location=location,
                        scraped_by=request.user,
                        source='BOSSJOB'
                    ).update(is_active=False)
                    
                    # Create new scraped job entry
                    scraped_job = ScrapedJob.objects.create(
                        search_keyword=keyword,
                        search_location=location,
                        source='BOSSJOB',
                        scraped_data=results,
                        total_found=results.get('total_found', 0),
                        scraped_by=request.user
                    )
                    logger.info(f"Scraped data saved to database with ID: {scraped_job.id}, previous entries deactivated")
                    
                except Exception as e:
                    logger.error(f"Error saving scraped data to database: {str(e)}")
                
                # Store job URLs in session for redirect functionality (more reliable than cache)
                job_urls = []
                for index, job in enumerate(results.get('jobs', [])):
                    url = job.get('url', '')
                    if url and url not in ['#', '#no-url-found', 'javascript:void(0)', '']:
                        # Ensure URL is absolute
                        if not url.startswith(('http://', 'https://')):
                            if url.startswith('/'):
                                url = f"https://bossjob.ph{url}"
                            else:
                                url = f"https://bossjob.ph/{url.lstrip('/')}"
                        job_urls.append(url)
                        logger.debug(f"Stored job URL {index}: {url}")
                    else:
                        job_urls.append(None)
                        logger.debug(f"Job {index} has no valid URL: {url}")
                
                # Store in session - persists across requests for the user
                request.session['job_scraper_urls'] = job_urls
                request.session.modified = True
                logger.info(f"Stored {len(job_urls)} job URLs in session (user: {request.user.username})")
                
                # Return the results as HTML fragment for HTMX
                return render(request, 'jobs/partials/job_scraper_results.html', {
                    'results': results,
                    'form': form
                })
                
            except Exception as e:
                logger.error(f"Error in job scraper: {str(e)}")
                error_results = {
                    'success': False,
                    'jobs': [],
                    'total_found': 0,
                    'error': 'An unexpected error occurred while fetching jobs.',
                    'message': 'Please try again later.'
                }
                return render(request, 'jobs/partials/job_scraper_results.html', {
                    'results': error_results,
                    'form': form
                })
    else:
        # Form validation errors
        error_results = {
            'success': False,
            'jobs': [],
            'total_found': 0,
            'error': 'Please correct the form errors below.',
            'message': 'Invalid form data'
        }
        return render(request, 'jobs/partials/job_scraper_results.html', {
            'results': error_results,
            'form': form
        })
    
    # If not POST, redirect to main scraper page
    return redirect('jobs:job_scraper')


@login_required
def job_redirect(request, job_id):
    """Redirect to the actual job URL on BossJob.ph with improved error handling"""
    try:
        # Get the job URL from session (more reliable than cache)
        job_urls = request.session.get('job_scraper_urls', [])
        
        # Debug logging
        logger.debug(f"Job redirect called with job_id: {job_id}, session has {len(job_urls)} URLs")
        logger.debug(f"Session URLs: {job_urls}")
        
        # Convert job_id to integer
        try:
            job_index = int(job_id)
        except (ValueError, TypeError):
            logger.error(f"Invalid job_id format: {job_id}")
            messages.error(request, "Invalid job link. Please search again.")
            return redirect('https://bossjob.ph/en-us/jobs-hiring')
        
        # Check if index is valid
        if not job_urls or job_index < 0 or job_index >= len(job_urls):
            logger.warning(f"Invalid job index: {job_index}, URLs count: {len(job_urls)}")
            messages.warning(request, "Job link not found. Redirecting to BossJob.ph job search.")
            return redirect('https://bossjob.ph/en-us/jobs-hiring')
        
        job_url = job_urls[job_index]
        logger.debug(f"Retrieved job URL for index {job_index}: {job_url}")
        
        if not job_url:
            logger.warning(f"Job URL is None for index {job_index}")
            messages.warning(request, "Job link not available. Redirecting to BossJob.ph job search.")
            return redirect('https://bossjob.ph/en-us/jobs-hiring')
        
        # Handle special markers - redirect to main bossjob page
        if job_url in ['#no-url-found', 'javascript:void(0)', '#', '#no-url-found']:
            logger.warning(f"Job URL is a special marker: {job_url}")
            messages.warning(request, "Direct job link is not available. Redirecting to BossJob.ph job search.")
            return redirect('https://bossjob.ph/en-us/jobs-hiring')
        
        # Validate URL format
        if not isinstance(job_url, str) or len(job_url.strip()) == 0:
            logger.warning(f"Job URL is invalid format: {type(job_url)} - {job_url}")
            messages.warning(request, "Invalid job link format. Redirecting to BossJob.ph job search.")
            return redirect('https://bossjob.ph/en-us/jobs-hiring')
        
        # Ensure the URL is a valid URL (starts with http:// or https://)
        if not job_url.startswith(('http://', 'https://')):
            # If it's a relative URL, prepend bossjob.ph base
            if job_url.startswith('/'):
                job_url = f"https://bossjob.ph{job_url}"
            else:
                logger.warning(f"Job URL is not absolute: {job_url}")
                messages.warning(request, "Invalid job link. Redirecting to BossJob.ph job search.")
                return redirect('https://bossjob.ph/en-us/jobs-hiring')
        
        # Log the redirect
        logger.info(f"Redirecting to job URL: {job_url} for job_index: {job_index}")
        
        # Skip URL validation for now - just redirect directly
        # URL validation was causing delays and failures
        # The user can verify the URL themselves
            
        # Redirect directly to the job URL
        return redirect(job_url)
        
    except Exception as e:
        logger.error(f"Error in job redirect: {str(e)}", exc_info=True)
        messages.error(request, "An error occurred while accessing the job link. Redirecting to BossJob.ph job search.")
        return redirect('https://bossjob.ph/en-us/jobs-hiring')
