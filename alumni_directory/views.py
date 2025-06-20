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

logger = logging.getLogger(__name__)

User = get_user_model()

def is_admin(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_admin)
@paginate(items_per_page=12)  # Show 12 alumni per page
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
            queryset = queryset.filter(
                Q(user__first_name__icontains=search_query) | 
                Q(user__last_name__icontains=search_query)
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
        logger.info(f"Alumni detail view accessed for ID: {pk}, Name: {alumni.full_name}")
        
        # Get profile
        profile = None
        if hasattr(alumni.user, 'profile'):
            profile = alumni.user.profile
            logger.info(f"Profile found for alumni ID: {pk}")
        else:
            logger.warning(f"No profile found for alumni ID: {pk}")
        
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

@user_passes_test(is_admin)
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

@user_passes_test(is_admin)
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

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [alumni.email],
            fail_silently=False,
        )
        
        logger.info(f"Profile completion reminder sent to alumni ID: {pk}")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Reminder sent successfully'
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

@user_passes_test(is_admin)
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
            
        # Export to CSV if requested
        if request.GET.get('format') == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="alumni_directory.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['ID', 'Full Name', 'Year', 'Course', 'Present Occupation', 'Company', 'Employment Address'])
            
            for alumni in queryset:
                # Get current experience for occupation and company
                current_exp = None
                if hasattr(alumni.user, 'profile'):
                    current_exp = alumni.user.profile.experience.filter(is_current=True).first()
                
                writer.writerow([
                    alumni.id,
                    alumni.full_name,
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
            'search_query': search_query,
            'selected_year': grad_year[0] if grad_year else None,
            'selected_course': course[0] if course else None,
        }
        
        return render(request, 'alumni_directory/tabular_alumni_list.html', context)
        
    except Exception as e:
        logger.error(f"Error in tabular_alumni_list view: {str(e)}")
        messages.error(request, "An error occurred while loading the alumni list.")
        return redirect('alumni_directory:alumni_list')
