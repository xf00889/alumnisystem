import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q, Count, F
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.contrib.auth import get_user_model
from .models import Alumni, AlumniDocument, Achievement, ProfessionalExperience
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from accounts.decorators import paginate
from django.contrib import messages
from accounts.models import Profile, Experience
from .forms import AlumniForm, AlumniFilterForm, AlumniSearchForm, AlumniDocumentForm
import csv
from datetime import datetime

logger = logging.getLogger(__name__)

User = get_user_model()

def apply_selective_export_filters(request, base_queryset=None):
    """
    Apply selective export filters and generate appropriate filename
    Returns tuple: (filtered_queryset, filename, has_selective_filters)
    """
    if base_queryset is None:
        export_queryset = Alumni.objects.select_related('user').all()
    else:
        export_queryset = base_queryset

    # Apply selective export filters
    export_colleges = request.GET.getlist('export_colleges')
    if export_colleges:
        export_queryset = export_queryset.filter(college__in=export_colleges)

    export_courses = request.GET.getlist('export_courses')
    if export_courses:
        export_queryset = export_queryset.filter(course__in=export_courses)

    export_years = request.GET.getlist('export_years')
    if export_years:
        export_queryset = export_queryset.filter(graduation_year__in=export_years)

    # Year range filters
    year_from = request.GET.get('export_year_from')
    year_to = request.GET.get('export_year_to')
    if year_from:
        export_queryset = export_queryset.filter(graduation_year__gte=year_from)
    if year_to:
        export_queryset = export_queryset.filter(graduation_year__lte=year_to)

    export_employment_status = request.GET.getlist('export_employment_status')
    if export_employment_status:
        export_queryset = export_queryset.filter(employment_status__in=export_employment_status)

    export_verification_status = request.GET.getlist('export_verification_status')
    if export_verification_status:
        # Convert string values to boolean
        verification_filters = []
        for status in export_verification_status:
            if status.lower() == 'true':
                verification_filters.append(True)
            elif status.lower() == 'false':
                verification_filters.append(False)
        if verification_filters:
            export_queryset = export_queryset.filter(is_verified__in=verification_filters)

    # Generate dynamic filename
    filename_parts = ['alumni']

    if export_colleges:
        college_codes = '_'.join(export_colleges)
        filename_parts.append(college_codes)

    if year_from or year_to or export_years:
        if year_from and year_to:
            filename_parts.append(f"{year_from}-{year_to}")
        elif export_years:
            if len(export_years) <= 3:
                filename_parts.append('_'.join(export_years))
            else:
                filename_parts.append(f"{min(export_years)}-{max(export_years)}")

    if export_employment_status and len(export_employment_status) < 5:
        emp_codes = '_'.join([status.split('_')[0] for status in export_employment_status])
        filename_parts.append(emp_codes)

    # Add timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename_parts.append(timestamp)

    filename = '_'.join(filename_parts) + '.csv'

    # Check if any selective filters were applied
    has_selective_filters = any([export_colleges, export_courses, export_years, year_from, year_to,
                                export_employment_status, export_verification_status])

    return export_queryset, filename, has_selective_filters

def is_admin(user):
    return user.is_authenticated and user.is_staff

@login_required
@paginate(per_page=12)  # Show 12 alumni per page
def alumni_list(request):
    try:
        # Get all unique values for filters
        graduation_years = Alumni.objects.values_list('graduation_year', flat=True).distinct().order_by('-graduation_year')
        courses = Alumni.objects.values_list('course', flat=True).distinct().order_by('course')
        provinces = Alumni.objects.values_list('province', flat=True).distinct().order_by('province')
        
        # Get counts for statistics
        graduation_years_count = graduation_years.count()
        courses_count = courses.count()
        provinces_count = provinces.count()
        
        # Base queryset with efficient loading
        queryset = Alumni.objects.select_related('user').all()
        logger.info(f"Initial alumni queryset count: {queryset.count()}")
        
        # Apply filters
        search_query = request.GET.get('search', '').strip()
        if search_query:
            # Create a lookup for college display names
            college_lookup = Q()
            for code, name in Alumni.COLLEGE_CHOICES:
                if search_query.lower() in name.lower():
                    college_lookup |= Q(college=code)

            queryset = queryset.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(course__icontains=search_query) |
                Q(city__icontains=search_query) |
                Q(province__icontains=search_query) |
                Q(current_company__icontains=search_query) |
                Q(job_title__icontains=search_query) |
                college_lookup  # Include college name search
            )
        
        # Graduation Year filter
        grad_year = request.GET.getlist('graduation_year')
        if grad_year:
            queryset = queryset.filter(graduation_year__in=grad_year)
        
        # Course filter
        course = request.GET.getlist('course')
        if course:
            queryset = queryset.filter(course__in=course)
        
        # College filter
        college = request.GET.getlist('college')
        if college:
            queryset = queryset.filter(college__in=college)
        
        # Campus filter
        campus = request.GET.getlist('campus')
        if campus:
            queryset = queryset.filter(campus__in=campus)
        
        # Location filter
        province = request.GET.getlist('province')
        if province:
            queryset = queryset.filter(province__in=province)
        
        # Employment Status filter
        employment_status = request.GET.getlist('employment_status')
        if employment_status:
            queryset = queryset.filter(employment_status__in=employment_status)
        
        # Count selected filters
        selected_filters_count = sum(
            bool(x) for x in [
                grad_year, course, college, campus, 
                province, employment_status, search_query
            ]
        )
        any_filter_active = selected_filters_count > 0
        
        # Get total counts
        total_alumni = Alumni.objects.count()
        total_registered = queryset.count()
        
        context = {
            'alumni_list': queryset,  # The decorator will paginate this
            'graduation_years': graduation_years,
            'courses': courses,
            'provinces': provinces,
            'colleges': Alumni.COLLEGE_CHOICES,
            'campuses': Alumni.CAMPUS_CHOICES,
            'employment_statuses': Alumni.EMPLOYMENT_STATUS_CHOICES,
            'selected_filters': {
                'graduation_year': grad_year,
                'course': course,
                'college': college,
                'campus': campus,
                'province': province,
                'employment_status': employment_status,
                'search': search_query,
            },
            'selected_filters_count': selected_filters_count,
            'any_filter_active': any_filter_active,
            'total_alumni': total_alumni,
            'total_registered': total_registered,
            'graduation_years_count': graduation_years_count,
            'courses_count': courses_count,
            'provinces_count': provinces_count
        }
        
        template_name = 'alumni_directory/alumni_list.html'
        if request.headers.get('HX-Request'):
            template_name = 'alumni_directory/partials/alumni_list.html'
        
        return render(request, template_name, context)
        
    except Exception as e:
        logger.error(f"Error in alumni_list view: {str(e)}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': 'An error occurred while loading the alumni list.'
            }, status=500)
        raise

@login_required
def alumni_detail(request, pk):
    try:
        # Get alumni object or 404
        alumni = get_object_or_404(Alumni, pk=pk)
        try:
            alumni_name = alumni.full_name
        except Exception:
            alumni_name = f"Alumni ID: {pk}"
            logger.warning(f"Could not get full name for alumni ID: {pk}")
        logger.info(f"Alumni detail view accessed for ID: {pk}, Name: {alumni_name}")
        
        # Get profile
        profile = None
        try:
            profile = alumni.user.profile
            logger.info(f"Profile found for alumni ID: {pk}")
        except Exception:
            # Profile doesn't exist or other error
            logger.warning(f"No profile found for alumni ID: {pk}")
            profile = None
        
        # Get documents from both AlumniDocument and accounts.Document models
        alumni_documents = list(alumni.documents.all().order_by('-uploaded_at'))
        profile_documents = []
        
        if profile:
            from accounts.models import Document
            
            # Create a wrapper class to make profile documents behave like AlumniDocuments
            class DocumentWrapper:
                def __init__(self, doc):
                    self.title = doc.title
                    self.document_type = doc.document_type
                    self.file = doc.file
                    self.uploaded_at = doc.uploaded_at
                    self.is_verified = doc.is_verified
                
                def get_document_type_display(self):
                    # Map document types from accounts.Document to display names
                    type_map = dict(Document.DOCUMENT_TYPES)
                    return type_map.get(self.document_type, self.document_type)
            
            # Wrap each profile document
            profile_docs = Document.objects.filter(profile=profile).order_by('-uploaded_at')
            profile_documents = [DocumentWrapper(doc) for doc in profile_docs]
            logger.info(f"Profile documents found: {len(profile_documents)}")
        
        # Combine documents from both sources
        combined_documents = alumni_documents + profile_documents
        
        # Calculate document stats
        total_documents = len(combined_documents)
        verified_documents = sum(1 for doc in combined_documents if hasattr(doc, 'is_verified') and doc.is_verified)
        pending_verification = total_documents - verified_documents
        
        logger.info(f"Documents for alumni ID {pk}: Total={total_documents}, Verified={verified_documents}, Pending={pending_verification}")
        
        # Debug: Check if documents exist in the database
        if total_documents == 0:
            logger.warning(f"No documents found for alumni ID: {pk}")
            # Check if there are any documents in the system at all
            all_docs_count = AlumniDocument.objects.count()
            logger.info(f"Total AlumniDocuments in system: {all_docs_count}")
            
            from accounts.models import Document
            all_profile_docs_count = Document.objects.count()
            logger.info(f"Total Profile Documents in system: {all_profile_docs_count}")
        
        # Get professional experiences using the ProfessionalExperience utility class
        unified_experience = ProfessionalExperience.get_unified_experience(alumni)
        career_path = ProfessionalExperience.get_career_path_only(alumni)
        work_experience = ProfessionalExperience.get_regular_experience_only(alumni)
        
        # Calculate profile completion percentage
        completion_fields = [
            alumni.gender,
            alumni.date_of_birth,
            alumni.phone_number,
            alumni.address,
            alumni.province,
            alumni.city,
            alumni.country,
            alumni.current_company,
            alumni.job_title,
            alumni.bio
        ]
        
        filled_fields = sum(1 for field in completion_fields if field)
        completion_percentage = int((filled_fields / len(completion_fields)) * 100)
        
        # Get achievements
        achievements = alumni.achievements_list.all().order_by('-date_achieved')
        
        # Check if current user is owner
        is_owner = request.user == alumni.user
        
        # Check if the user is staff/admin
        is_admin = request.user.is_staff
        
        context = {
            'alumni': alumni,
            'profile': profile,
            'documents': combined_documents,
            'total_documents': total_documents,
            'verified_documents': verified_documents,
            'pending_verification': pending_verification,
            'completion_percentage': completion_percentage,
            'unified_experience': unified_experience,
            'career_path': career_path,
            'work_experience': work_experience,
            'achievements': achievements,
            'is_owner': is_owner,
            'is_admin': is_admin
        }
        
        return render(request, 'alumni_directory/alumni_detail.html', context)
        
    except Exception as e:
        logger.error(f"Error in alumni_detail view: {str(e)}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': 'An error occurred while loading the alumni details.'
            }, status=500)
        raise

@user_passes_test(is_admin, login_url='account_login')
def download_document(request, doc_id):
    try:
        document = get_object_or_404(AlumniDocument, id=doc_id)
        
        # Verify the document exists and is accessible
        if not document.file:
            logger.warning(f"Document {doc_id} has no file attached")
            return JsonResponse({
                'status': 'error',
                'message': 'Document file not found.'
            }, status=404)
        
        logger.info(f"Document download requested for ID: {doc_id}")
        
        response = JsonResponse({
            'status': 'success',
            'url': document.file.url,
            'filename': document.file.name.split('/')[-1]
        })
        
        return response
        
    except Exception as e:
        logger.error(f"Error in download_document view for doc ID {doc_id}: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred while processing the document download.'
        }, status=500)

@user_passes_test(is_admin, login_url='account_login')
def send_reminder(request, pk):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
        
    try:
        alumni = get_object_or_404(Alumni.objects.select_related('user'), pk=pk)
        
        # Get missing fields
        required_fields = [
            alumni.gender, alumni.date_of_birth, alumni.phone_number,
            alumni.province, alumni.city, alumni.address,
            alumni.graduation_year, alumni.course
        ]
        optional_fields = [
            alumni.alternate_email, alumni.linkedin_profile,
            alumni.major, alumni.honors, alumni.current_company,
            alumni.job_title, alumni.industry, alumni.skills,
            alumni.interests, alumni.bio, alumni.achievements
        ]
        
        completed_required = sum(1 for field in required_fields if field)
        completed_optional = sum(1 for field in optional_fields if field)
        
        # Get missing sections
        empty_sections = []
        if not any([alumni.phone_number, alumni.alternate_email, alumni.linkedin_profile]):
            empty_sections.append('Personal Information')
        if not any([alumni.province, alumni.city, alumni.address]):
            empty_sections.append('Location Information')
        if not any([alumni.current_company, alumni.job_title, alumni.industry]):
            empty_sections.append('Professional Information')
        if not any([alumni.major, alumni.honors]):
            empty_sections.append('Academic Information')
        if not alumni.skills:
            empty_sections.append('Skills')
        if not alumni.interests:
            empty_sections.append('Interests')
        if not alumni.documents.exists():
            empty_sections.append('Documents')
        if not any([alumni.bio, alumni.achievements]):
            empty_sections.append('Additional Information')
        
        # Send email
        subject = 'Complete Your Alumni Profile'
        message = f"""Dear {alumni.full_name},

We noticed that your alumni profile is incomplete. Please take a moment to update your profile with the following missing information:

{chr(10).join('- ' + section for section in empty_sections)}

Completing your profile helps us better serve the alumni community and keep you connected with opportunities.

Required Fields Completed: {(completed_required / len(required_fields)) * 100:.0f}%
Optional Fields Completed: {(completed_optional / len(optional_fields)) * 100:.0f}%

Click here to update your profile: {request.build_absolute_uri(reverse('accounts:profile'))}

Best regards,
The Alumni Team"""

        from core.email_utils import send_email_with_provider
        
        success = send_email_with_provider(
            subject=subject,
            message=message,
            recipient_list=[alumni.email],
            from_email=settings.DEFAULT_FROM_EMAIL,
            fail_silently=False
        )
        
        if success:
            logger.info(f"Profile completion reminder sent to alumni ID: {pk}")
            return JsonResponse({
                'status': 'success',
                'message': 'Reminder sent successfully'
            })
        else:
            logger.error(f"Failed to send profile completion reminder to alumni ID: {pk}")
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to send reminder'
            })
        
    except Alumni.DoesNotExist:
        logger.error(f"Alumni with ID {pk} not found")
        return JsonResponse({
            'status': 'error',
            'message': 'Alumni not found'
        }, status=404)
        
    except Exception as e:
        logger.error(f"Error sending reminder to alumni ID {pk}: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to send reminder'
        }, status=500)

@login_required
def tabular_alumni_list(request):
    """
    Display alumni in a tabular format with specific columns.
    """
    try:
        # Base queryset with efficient loading
        queryset = Alumni.objects.select_related('user').all()
        
        # Apply filters
        search_query = request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search_query) | 
                Q(user__last_name__icontains=search_query) |
                Q(course__icontains=search_query) |
                Q(city__icontains=search_query) |
                Q(province__icontains=search_query)
            )
        
        # Graduation Year filter
        grad_year = request.GET.getlist('graduation_year')
        if grad_year:
            queryset = queryset.filter(graduation_year__in=grad_year)
        
        # Course filter
        course = request.GET.getlist('course')
        if course:
            queryset = queryset.filter(course__in=course)

        # College filter
        college = request.GET.getlist('college')
        if college:
            queryset = queryset.filter(college__in=college)
            
        # Export to CSV if requested
        if request.GET.get('format') == 'csv':
            # Apply selective export filters
            export_queryset, filename, has_selective_filters = apply_selective_export_filters(request)

            # If no selective filters are applied, use the current filtered queryset
            if not has_selective_filters:
                export_queryset = queryset
                filename = f"alumni_directory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'

            writer = csv.writer(response)
            writer.writerow(['ID', 'Full Name', 'College', 'Year', 'Course', 'Present Occupation', 'Company', 'Employment Address'])

            for alumni in export_queryset:
                # Get current experience for occupation and company
                current_exp = None
                if hasattr(alumni.user, 'profile'):
                    current_exp = alumni.user.profile.experience.filter(is_current=True).first()

                writer.writerow([
                    alumni.id,
                    alumni.full_name,
                    alumni.college_display if alumni.college else 'Not specified',
                    alumni.graduation_year,
                    alumni.course,
                    current_exp.position if current_exp else alumni.job_title,
                    current_exp.company if current_exp else alumni.current_company,
                    current_exp.location if current_exp else f"{alumni.city}, {alumni.province}"
                ])

            return response
        
        # Pagination
        paginator = Paginator(queryset, 25)  # 25 items per page
        page_number = request.GET.get('page')
        alumni_page = paginator.get_page(page_number)
        
        # Get counts for filtering dropdown options
        graduation_years = Alumni.objects.values_list('graduation_year', flat=True).distinct().order_by('-graduation_year')
        courses = Alumni.objects.values_list('course', flat=True).distinct().order_by('course')
        
        context = {
            'alumni_list': alumni_page,
            'graduation_years': graduation_years,
            'courses': courses,
            'colleges': Alumni.COLLEGE_CHOICES,
            'search_query': search_query,
            'selected_year': grad_year[0] if grad_year else None,
            'selected_course': course[0] if course else None,
            'selected_college': college[0] if college else None,
        }
        
        return render(request, 'alumni_directory/tabular_alumni_list.html', context)
        
    except Exception as e:
        logger.error(f"Error in tabular_alumni_list view: {str(e)}")
        messages.error(request, "An error occurred while loading the alumni list.")
        return redirect('alumni_directory:alumni_list')

@user_passes_test(is_admin, login_url='account_login')
def alumni_management(request):
    """
    Alumni Management view with tabular display, import/export functionality.
    """
    try:
        # Handle CSV import
        if request.method == 'POST' and 'import_csv' in request.POST:
            csv_file = request.FILES.get('csv_file')
            if csv_file:
                try:
                    # Read CSV file
                    decoded_file = csv_file.read().decode('utf-8')
                    csv_data = csv.DictReader(decoded_file.splitlines())
                    
                    imported_count = 0
                    updated_count = 0
                    
                    for row in csv_data:
                        # Extract data from CSV row
                        full_name = row.get('Full Name', '').strip()
                        graduation_year = row.get('Year', '').strip()
                        course = row.get('Course', '').strip()
                        occupation = row.get('Present Occupation', '').strip()
                        company = row.get('Name of Company', '').strip()
                        address = row.get('Employment Address', '').strip()
                        
                        if full_name and graduation_year:
                            # Split full name into first and last name
                            name_parts = full_name.split(' ', 1)
                            first_name = name_parts[0]
                            last_name = name_parts[1] if len(name_parts) > 1 else ''
                            
                            # Try to find existing alumni by name and graduation year
                            try:
                                alumni = Alumni.objects.get(
                                    user__first_name__iexact=first_name,
                                    user__last_name__iexact=last_name,
                                    graduation_year=graduation_year
                                )
                                # Update existing alumni
                                alumni.course = course
                                alumni.job_title = occupation
                                alumni.current_company = company
                                if address:
                                    address_parts = address.split(', ')
                                    if len(address_parts) >= 2:
                                        alumni.city = address_parts[0]
                                        alumni.province = address_parts[1]
                                alumni.save()
                                updated_count += 1
                            except Alumni.DoesNotExist:
                                # Create new user and alumni
                                user = User.objects.create_user(
                                    username=f"{first_name.lower()}.{last_name.lower()}.{graduation_year}",
                                    first_name=first_name,
                                    last_name=last_name,
                                    email=f"{first_name.lower()}.{last_name.lower()}@example.com"
                                )
                                
                                alumni = Alumni.objects.create(
                                    user=user,
                                    graduation_year=graduation_year,
                                    course=course,
                                    job_title=occupation,
                                    current_company=company
                                )
                                
                                if address:
                                    address_parts = address.split(', ')
                                    if len(address_parts) >= 2:
                                        alumni.city = address_parts[0]
                                        alumni.province = address_parts[1]
                                        alumni.save()
                                
                                imported_count += 1
                    
                    messages.success(request, f"Successfully imported {imported_count} new alumni and updated {updated_count} existing records.")
                    
                except Exception as e:
                    logger.error(f"Error importing CSV: {str(e)}")
                    messages.error(request, f"Error importing CSV file: {str(e)}")
            else:
                messages.error(request, "Please select a CSV file to import.")
        
        # Base queryset with efficient loading
        queryset = Alumni.objects.select_related('user').all()
        
        # Apply filters
        search_query = request.GET.get('search', '').strip()
        if search_query:
            # Create a lookup for college display names
            college_lookup = Q()
            for code, name in Alumni.COLLEGE_CHOICES:
                if search_query.lower() in name.lower():
                    college_lookup |= Q(college=code)

            queryset = queryset.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(course__icontains=search_query) |
                Q(city__icontains=search_query) |
                Q(province__icontains=search_query) |
                Q(current_company__icontains=search_query) |
                Q(job_title__icontains=search_query) |
                college_lookup  # Include college name search
            )
        
        # Graduation Year filter
        grad_year = request.GET.getlist('graduation_year')
        if grad_year:
            queryset = queryset.filter(graduation_year__in=grad_year)
        
        # Course filter
        course = request.GET.getlist('course')
        if course:
            queryset = queryset.filter(course__in=course)

        # College filter
        college = request.GET.getlist('college')
        if college:
            queryset = queryset.filter(college__in=college)
            
        # Export to CSV if requested
        if request.GET.get('format') == 'csv':
            # Apply selective export filters
            export_queryset, filename, has_selective_filters = apply_selective_export_filters(request)

            # If no selective filters are applied, use the current filtered queryset
            if not has_selective_filters:
                export_queryset = queryset
                filename = f"alumni_management_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'

            writer = csv.writer(response)
            writer.writerow(['ID', 'Full Name', 'College', 'Year', 'Course', 'Present Occupation', 'Name of Company', 'Employment Address'])

            for alumni in export_queryset:
                # Get current experience for occupation and company
                current_exp = None
                if hasattr(alumni.user, 'profile'):
                    current_exp = alumni.user.profile.experience.filter(is_current=True).first()

                writer.writerow([
                    alumni.id,
                    alumni.full_name,
                    alumni.college_display if alumni.college else 'Not specified',
                    alumni.graduation_year,
                    alumni.course,
                    current_exp.position if current_exp else alumni.job_title,
                    current_exp.company if current_exp else alumni.current_company,
                    current_exp.location if current_exp else f"{alumni.city}, {alumni.province}" if alumni.city and alumni.province else ""
                ])

            return response
        
        # Pagination
        paginator = Paginator(queryset, 25)  # 25 items per page
        page_number = request.GET.get('page')
        alumni_page = paginator.get_page(page_number)
        
        # Get counts for filtering dropdown options
        graduation_years = Alumni.objects.values_list('graduation_year', flat=True).distinct().order_by('-graduation_year')
        courses = Alumni.objects.values_list('course', flat=True).distinct().order_by('course')
        
        context = {
            'alumni_list': alumni_page,
            'graduation_years': graduation_years,
            'courses': courses,
            'colleges': Alumni.COLLEGE_CHOICES,
            'search_query': search_query,
            'selected_year': grad_year[0] if grad_year else None,
            'selected_course': course[0] if course else None,
            'selected_college': college[0] if college else None,
        }
        
        return render(request, 'alumni_directory/alumni_management.html', context)
        
    except Exception as e:
        logger.error(f"Error in alumni_management view: {str(e)}")
        messages.error(request, "An error occurred while loading the alumni management page.")
        return redirect('alumni_directory:alumni_list')

@user_passes_test(is_admin, login_url='account_login')
def alumni_detail_modal(request, pk):
    """
    Return alumni detail content for modal display.
    """
    try:
        alumni = get_object_or_404(Alumni, pk=pk)
        logger.info(f"Alumni detail modal accessed for ID: {pk}, Name: {alumni.full_name}")

        # Get profile
        profile = None
        unified_experience = []
        if hasattr(alumni.user, 'profile'):
            profile = alumni.user.profile

            # Get all experience entries, appropriately sorted
            unified_experience = profile.experience.all().order_by('-is_current', '-start_date')

        # Get documents from both AlumniDocument and accounts.Document models
        alumni_documents = list(alumni.documents.all().order_by('-uploaded_at'))
        profile_documents = []

        if profile:
            from accounts.models import Document

            # Create a wrapper class to make profile documents behave like AlumniDocuments
            class DocumentWrapper:
                def __init__(self, doc):
                    self.id = doc.id
                    self.title = doc.title
                    self.document_type = doc.document_type
                    self.file = doc.file
                    self.uploaded_at = doc.uploaded_at
                    self.is_verified = doc.is_verified
                    self.file_size = self._get_file_size()

                def _get_file_size(self):
                    try:
                        if self.file and hasattr(self.file, 'size'):
                            size = self.file.size
                            if size < 1024:
                                return f"{size} B"
                            elif size < 1024 * 1024:
                                return f"{size / 1024:.1f} KB"
                            else:
                                return f"{size / (1024 * 1024):.1f} MB"
                    except:
                        pass
                    return "Unknown size"

                def get_document_type_display(self):
                    # Map document types from accounts.Document to display names
                    type_map = dict(Document.DOCUMENT_TYPES)
                    return type_map.get(self.document_type, self.document_type)

            # Wrap each profile document
            profile_docs = Document.objects.filter(profile=profile).order_by('-uploaded_at')
            profile_documents = [DocumentWrapper(doc) for doc in profile_docs]

        # Combine documents from both sources
        combined_documents = alumni_documents + profile_documents

        # Group documents by type for template
        documents_by_type = {}
        for doc in combined_documents:
            doc_type = doc.document_type
            if doc_type not in documents_by_type:
                documents_by_type[doc_type] = []
            documents_by_type[doc_type].append(doc)

        # Document types for template iteration
        document_types = [
            ('RESUME', 'Resume/CV'),
            ('CERT', 'Certification'),
            ('DIPLOMA', 'Diploma'),
            ('TOR', 'Transcript of Records'),
            ('TRANSCRIPT', 'Academic Transcript'),
            ('CERTIFICATE', 'Certificate'),
            ('OTHER', 'Other'),
        ]

        # Calculate document stats
        total_documents = len(combined_documents)
        verified_documents = sum(1 for doc in combined_documents if hasattr(doc, 'is_verified') and doc.is_verified)
        pending_verification = total_documents - verified_documents

        doc_stats = {
            'total': total_documents,
            'verified': verified_documents,
            'pending': pending_verification
        }

        # Calculate profile completion
        required_fields = [
            alumni.gender, alumni.date_of_birth, alumni.phone_number,
            alumni.province, alumni.city, alumni.address,
            alumni.graduation_year, alumni.course
        ]
        optional_fields = [
            alumni.alternate_email, alumni.linkedin_profile,
            alumni.major, alumni.honors, alumni.current_company,
            alumni.job_title, alumni.industry, alumni.skills,
            alumni.interests, alumni.bio, alumni.achievements
        ]

        completed_required = sum(1 for field in required_fields if field)
        completed_optional = sum(1 for field in optional_fields if field)

        required_percentage = (completed_required / len(required_fields)) * 100
        optional_percentage = (completed_optional / len(optional_fields)) * 100
        total_percentage = (required_percentage + optional_percentage) / 2

        profile_completion = {
            'required': required_percentage,
            'optional': optional_percentage,
            'total': total_percentage
        }

        # Determine empty sections
        empty_sections = {
            'personal': not any([alumni.phone_number, alumni.alternate_email, alumni.linkedin_profile]),
            'location': not any([alumni.province, alumni.city, alumni.address]),
            'professional': not any([alumni.current_company, alumni.job_title, alumni.industry]),
            'academic': not any([alumni.major, alumni.honors]),
            'skills': not alumni.skills,
            'interests': not alumni.interests,
            'documents': not combined_documents,
            'additional': not any([alumni.bio, alumni.achievements])
        }

        # Get achievements
        achievements = alumni.achievements_list.all().order_by('-date_achieved')

        context = {
            'alumni': alumni,
            'profile': profile,
            'unified_experience': unified_experience,
            'achievements': achievements,
            'documents': documents_by_type,
            'document_types': document_types,
            'doc_stats': doc_stats,
            'profile_completion': profile_completion,
            'empty_sections': empty_sections,
        }

        return render(request, 'alumni_directory/partials/alumni_detail_modal.html', context)

    except Exception as e:
        logger.error(f"Error in alumni_detail_modal view: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred while loading the alumni details.'
        }, status=500)
