import logging
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from .models import Alumni, AlumniDocument
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import Http404
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings

logger = logging.getLogger(__name__)

User = get_user_model()

def is_admin(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_admin)
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
        
        # Pagination
        try:
            page = int(request.GET.get('page', 1))
        except ValueError:
            page = 1
            
        paginator = Paginator(queryset, 24)
        try:
            alumni = paginator.page(page)
        except Exception as e:
            alumni = paginator.page(1)
            logger.warning(f"Pagination error: {str(e)}. Defaulting to first page.")
        
        # Get total counts for summary
        total_alumni = queryset.count()
        total_registered = Alumni.objects.count()
        
        # Calculate total active filters
        selected_filters_count = sum(
            bool(filters) for filters in [
                grad_year, course, college, campus, 
                province, employment_status, search_query
            ]
        )
        
        # Check if any filter is active
        any_filter_active = selected_filters_count > 0
        
        logger.info(f"Filtered alumni count: {total_alumni}")
        
        context = {
            'alumni_list': alumni,
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

@user_passes_test(is_admin)
def alumni_detail(request, pk):
    try:
        # Optimize query with select_related and prefetch_related
        alumni = get_object_or_404(
            Alumni.objects.select_related(
                'user',
                'user__profile'
            ).prefetch_related(
                'documents'
            ),
            pk=pk
        )
        
        # Ensure profile exists before proceeding
        try:
            profile = alumni.user.profile
        except (Alumni.user.RelatedObjectDoesNotExist, AttributeError):
            from accounts.models import Profile
            with transaction.atomic():
                profile = Profile.objects.create(user=alumni.user)
                alumni.user.refresh_from_db()
            logger.info(f"Created missing profile for alumni ID: {pk}")
        
        # Get documents with efficient loading and categorization
        documents = {
            'RESUME': [],
            'CERT': [],
            'DIPLOMA': [],
            'TOR': [],
            'OTHER': []
        }
        
        try:
            for doc in alumni.documents.select_related('alumni').all():
                if doc.document_type in documents:
                    documents[doc.document_type].append(doc)
        except Exception as e:
            logger.error(f"Error loading documents for alumni {pk}: {str(e)}")
            documents = {k: [] for k in documents.keys()}
        
        # Get document statistics
        try:
            doc_stats = {
                'total': alumni.documents.count(),
                'verified': alumni.documents.filter(is_verified=True).count(),
                'pending': alumni.documents.filter(is_verified=False).count()
            }
        except Exception as e:
            logger.error(f"Error calculating document stats for alumni {pk}: {str(e)}")
            doc_stats = {'total': 0, 'verified': 0, 'pending': 0}
        
        # Get profile completion percentage with error handling
        try:
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
            
            profile_completion = {
                'required': (completed_required / len(required_fields)) * 100,
                'optional': (completed_optional / len(optional_fields)) * 100,
                'total': ((completed_required + completed_optional) / (len(required_fields) + len(optional_fields))) * 100
            }
        except Exception as e:
            logger.error(f"Error calculating profile completion for alumni {pk}: {str(e)}")
            profile_completion = {'required': 0, 'optional': 0, 'total': 0}
        
        context = {
            'alumni': alumni,
            'profile': profile,
            'documents': documents,
            'doc_stats': doc_stats,
            'profile_completion': profile_completion,
            'document_types': AlumniDocument.DOCUMENT_TYPES,
            'empty_sections': {
                'personal': not any([alumni.phone_number, alumni.alternate_email, alumni.linkedin_profile]),
                'location': not any([alumni.province, alumni.city, alumni.address]),
                'professional': not any([alumni.current_company, alumni.job_title, alumni.industry]),
                'academic': not any([alumni.major, alumni.honors]),
                'skills': not alumni.skills,
                'interests': not alumni.interests,
                'documents': not doc_stats['total'],
                'additional': not any([alumni.bio, alumni.achievements])
            }
        }

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'html': render(request, 'alumni_directory/partials/alumni_detail_content.html', context).content.decode('utf-8')
            })
        
        return render(request, 'alumni_directory/alumni_detail.html', context)
        
    except Exception as e:
        logger.error(f"Error in alumni_detail view for ID {pk}: {str(e)}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': 'An error occurred while loading the alumni details. Please try again.',
                'details': str(e)
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
