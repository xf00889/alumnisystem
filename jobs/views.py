from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from .models import JobPosting, JobApplication, RequiredDocument
from .forms import JobPostingForm, JobApplicationForm, RequiredDocumentFormSet
from .utils import calculate_job_match_score, get_skill_recommendations
from accounts.models import Profile, SkillMatch
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side
from .crawler.manager import CrawlerManager
import logging
from jobs.management.commands.crawl_diverse_jobs import Command as CrawlDiverseJobsCommand

logger = logging.getLogger(__name__)

def is_hr_or_admin(user):
    """Check if user is HR or admin"""
    return user.is_superuser or user.groups.filter(name='HR').exists()

def job_list(request):
    jobs = JobPosting.objects.filter(is_active=True)
    
    # Search functionality
    query = request.GET.get('q')
    if query:
        jobs = jobs.filter(
            Q(job_title__icontains=query) |
            Q(company_name__icontains=query) |
            Q(location__icontains=query) |
            Q(job_description__icontains=query)
        )
    
    # Filtering
    job_type = request.GET.get('job_type')
    source_type = request.GET.get('source_type')
    
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    if source_type:
        jobs = jobs.filter(source_type=source_type)
    
    # Skill-based view toggle
    skill_based_view = request.GET.get('skill_based', 'false').lower() == 'true'
    
    # Get user profile if authenticated and skill-based view is enabled
    user_profile = None
    job_matches = []
    recommended_skills = []
    
    if request.user.is_authenticated and skill_based_view:
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
    if skill_based_view and job_matches:
        # Already sorted by match score above
        pass
    elif sort == 'oldest':
        jobs = jobs.order_by('posted_date')
    else:  # newest first is default
        jobs = jobs.order_by('-posted_date')
    
    # Featured jobs
    featured_jobs = jobs.filter(is_featured=True)[:5]
    
    # For skill-based view, use the job_matches list
    if skill_based_view and user_profile:
        paginator = Paginator([match['job'] for match in job_matches], 10)
        page = request.GET.get('page')
        jobs_page = paginator.get_page(page)
        
        # Create a map for easy lookup of match data
        match_data = {match['job'].id: match for match in job_matches}
    else:
        # Pagination for regular view
        paginator = Paginator(jobs, 10)
        page = request.GET.get('page')
        jobs_page = paginator.get_page(page)
        match_data = {}
    
    context = {
        'jobs': jobs_page,
        'featured_jobs': featured_jobs,
        'current_query': query,
        'current_job_type': job_type,
        'current_source_type': source_type,
        'current_sort': sort,
        'job_types': JobPosting.JOB_TYPE_CHOICES,
        'source_types': JobPosting.SOURCE_TYPE_CHOICES,
        'skill_based_view': skill_based_view,
        'match_data': match_data,
        'recommended_skills': recommended_skills[:5] if recommended_skills else []  # Show top 5 recommendations
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
        
        # Send email
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[application.applicant.email],
                fail_silently=False,
            )
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
def crawl_jobs_view(request):
    """View to initiate job crawling from the web interface"""
    if request.method == 'POST':
        source = request.POST.get('source', '').strip().lower()
        query = request.POST.get('query', '').strip()
        location = request.POST.get('location', '').strip()
        max_jobs = int(request.POST.get('max_jobs', 25))
        job_type = request.POST.get('job_type', '').strip() or None
        
        if not source or not query:
            messages.error(request, "Job source and query are required.")
            return redirect('jobs:manage_jobs')
        
        try:
            # Initialize crawler manager
            manager = CrawlerManager()
            
            # Check if the source is supported
            available_sources = manager.list_available_sources()
            if source not in available_sources:
                messages.error(request, f"Unsupported job source: {source}")
                return redirect('jobs:manage_jobs')
            
            # Additional parameters
            params = {'max_jobs': max_jobs}
            if job_type:
                params['job_type'] = job_type
            
            # Log the crawling parameters
            logger.info(f"Starting job crawl from web interface: source={source}, query={query}, location={location}, max_jobs={max_jobs}")
            
            # Search for jobs
            results = manager.search_and_save_jobs(
                source=source,
                query=query,
                location=location,
                **params
            )
            
            # Generate summary
            created_count = sum(1 for r in results if r.get('created', False))
            updated_count = len(results) - created_count
            
            messages.success(
                request, 
                f"Successfully processed {len(results)} jobs "
                f"({created_count} created, {updated_count} updated)"
            )
            
        except Exception as e:
            logger.error(f"Job crawl failed from web interface: {str(e)}")
            messages.error(request, f"Job crawl failed: {str(e)}")
        
        return redirect('jobs:manage_jobs')
    
    # GET request shows the form
    context = {
        'sources': CrawlerManager().list_available_sources(),
        'job_types': JobPosting.JOB_TYPE_CHOICES,
    }
    return render(request, 'jobs/crawl_jobs.html', context)

@login_required
@user_passes_test(is_hr_or_admin)
def crawl_diverse_jobs_view(request):
    """View to initiate diverse job crawling from the web interface"""
    if request.method == 'POST':
        source = request.POST.get('source', '').strip().lower()
        location = request.POST.get('location', '').strip()
        category = request.POST.get('category', '').strip() or None
        max_jobs_per_category = int(request.POST.get('max_jobs_per_category', 10))
        job_type = request.POST.get('job_type', '').strip() or None
        
        if not source:
            messages.error(request, "Job source is required.")
            return redirect('jobs:crawl_diverse_jobs')
        
        try:
            # Initialize crawler manager
            manager = CrawlerManager()
            
            # Check if the source is supported
            available_sources = manager.list_available_sources()
            if source not in available_sources:
                messages.error(request, f"Unsupported job source: {source}")
                return redirect('jobs:crawl_diverse_jobs')
            
            # Get the job categories
            job_categories = CrawlDiverseJobsCommand.JOB_CATEGORIES
            
            # Process categories
            categories_to_process = {}
            if category:
                # Process only the specified category
                if category.lower() in job_categories:
                    categories_to_process[category.lower()] = job_categories[category.lower()]
                else:
                    messages.error(request, f"Unsupported category: {category}")
                    return redirect('jobs:crawl_diverse_jobs')
            else:
                # Process all categories
                categories_to_process = job_categories
            
            total_jobs_found = 0
            total_jobs_created = 0
            total_jobs_updated = 0
            
            # Start processing categories
            for category_name, search_terms in categories_to_process.items():
                category_jobs_found = 0
                category_jobs_created = 0
                category_jobs_updated = 0
                
                for search_term in search_terms:
                    try:
                        # Search for jobs
                        search_kwargs = {
                            'max_jobs': max_jobs_per_category
                        }
                        
                        if job_type:
                            search_kwargs['job_type'] = job_type
                        
                        results = manager.search_and_save_jobs(
                            source=source,
                            query=search_term,
                            location=location,
                            category=category_name,  # Pass category separately
                            **search_kwargs
                        )
                        
                        # Count results
                        jobs_found = len(results)
                        jobs_created = sum(1 for r in results if r.get('created', False))
                        jobs_updated = jobs_found - jobs_created
                        
                        # Add to totals
                        category_jobs_found += jobs_found
                        category_jobs_created += jobs_created
                        category_jobs_updated += jobs_updated
                        
                    except Exception as e:
                        logger.error(f"Error crawling jobs for '{search_term}' in category '{category_name}': {str(e)}")
                
                # Add to overall totals
                total_jobs_found += category_jobs_found
                total_jobs_created += category_jobs_created
                total_jobs_updated += category_jobs_updated
                
                # Log category results
                logger.info(f"Category {category_name}: {category_jobs_found} jobs ({category_jobs_created} created, {category_jobs_updated} updated)")
            
            # Display success message
            messages.success(
                request, 
                f"Successfully processed {total_jobs_found} jobs across {len(categories_to_process)} categories "
                f"({total_jobs_created} created, {total_jobs_updated} updated)"
            )
            
        except Exception as e:
            logger.error(f"Job crawl failed: {str(e)}")
            messages.error(request, f"Job crawl failed: {str(e)}")
        
        return redirect('jobs:manage_jobs')
    
    # GET request shows the form
    context = {
        'sources': CrawlerManager().list_available_sources(),
        'job_types': JobPosting.JOB_TYPE_CHOICES,
        'categories': JobPosting.CATEGORY_CHOICES,
    }
    return render(request, 'jobs/crawl_diverse_jobs.html', context)
