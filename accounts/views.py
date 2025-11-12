from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, UpdateView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponseForbidden
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST
from django.contrib import messages
from .decorators import email_verified_required
import logging

logger = logging.getLogger(__name__)
from .models import (
    Profile, Education, Experience, Skill, Document, SkillMatch,
    MentorApplication, Mentor, MentorReactivationRequest
)
from alumni_groups.models import AlumniGroup, GroupMembership
from alumni_directory.models import Alumni, Achievement, AlumniDocument, ProfessionalExperience
from .forms import (
    ProfileUpdateForm, 
    EducationFormSet, 
    ExperienceFormSet, 
    SkillFormSet,
    TranscriptUploadForm,
    CertificateUploadForm,
    DiplomaUploadForm,
    ResumeUploadForm,
    UserUpdateForm,
    PostRegistrationForm,
    EducationForm,
    ExperienceForm,
    SkillForm,
    DocumentUploadForm,
    MentorApplicationForm
)
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.db import transaction
from django.contrib import messages
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .serializers import (
    SkillSerializer, ProfileSkillsSerializer, SkillMatchSerializer,
    SkillMatchCalculationSerializer
)
from django.contrib.auth.decorators import user_passes_test
from .decorators import paginate
from django.contrib.contenttypes.models import ContentType
from log_viewer.models import AuditLog
from core.models.notifications import Notification

@email_verified_required
def post_registration(request):
    # First, ensure the user has a profile
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)

    # Redirect if already completed registration
    if profile.has_completed_registration:
        return redirect('core:home')
    
    # Check if there's a verification success message to display
    verification_success = request.session.get('verification_success', False)
    verification_message = request.session.get('verification_message', '')
    
    # Clear the session variables after reading them
    if verification_success:
        request.session.pop('verification_success', None)
        request.session.pop('verification_message', None)

    if request.method == 'POST':
        form = PostRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Save the form data
                    form.save(request.user)
                    
                    # Log registration completion
                    logger.info(
                        f"Registration completed: User ID={request.user.id}, Email={request.user.email}",
                        extra={
                            'user_id': request.user.id,
                            'user_email': request.user.email,
                            'action': 'registration_complete'
                        }
                    )
                    
                    messages.success(request, 'Registration completed successfully!')
                return redirect('core:home')
            except Exception as e:
                logger.error(
                    f"Error completing registration: {str(e)}",
                    extra={
                        'user_id': request.user.id,
                        'error_type': type(e).__name__
                    },
                    exc_info=True
                )
                messages.error(request, f'An error occurred: {str(e)}')
                raise
    else:
        # Pre-fill form with existing user data
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
        }
        # Get primary education if it exists
        try:
            education = Education.objects.get(profile=request.user.profile, is_primary=True)
            initial_data.update({
                'course_graduated': education.program,
                'graduation_year': education.graduation_year,
            })
            
            # Get current employment if exists
            current_exp = profile.experience.filter(is_current=True).first()
            if current_exp:
                initial_data.update({
                    'present_occupation': current_exp.position,
                    'company_name': current_exp.company,
                })
        except Education.DoesNotExist:
            pass

        form = PostRegistrationForm(initial=initial_data)

    return render(request, 'accounts/post_registration.html', {
        'form': form,
        'title': 'Complete Registration',
        'verification_success': verification_success,
        'verification_message': verification_message,
    })

@login_required
def profile_detail(request, username=None):
    try:
        # If username is provided, get that user's profile, otherwise get the logged-in user's profile
        if username:
            user = get_object_or_404(User, username=username)
            try:
                profile = user.profile
            except Profile.DoesNotExist:
                # Create profile if it doesn't exist
                profile = Profile.objects.create(user=user)
        else:
            try:
                profile = request.user.profile
            except Profile.DoesNotExist:
                # Create profile if it doesn't exist
                profile = Profile.objects.create(user=request.user)
            
        education_list = profile.education.all().order_by('-graduation_year')
        
        # Ensure current position is in experience list
        if profile.current_position and profile.current_employer:
            current_exp = profile.experience.filter(is_current=True).first()
            if not current_exp:
                # Create a current experience record if it doesn't exist
                import datetime
                current_exp = Experience.objects.create(
                    profile=profile,
                    position=profile.current_position,
                    company=profile.current_employer,
                    location=profile.city or '',
                    start_date=datetime.date.today(),
                    is_current=True,
                    career_significance='REGULAR'
                )
        
        # Get all experience entries, appropriately sorted
        experience_list = profile.experience.all().order_by('-is_current', '-start_date')
        
        # Split experiences for different tabs
        career_path_items = profile.experience.exclude(career_significance='REGULAR').order_by('-is_current', '-start_date')
        work_experience_items = profile.experience.filter(career_significance='REGULAR').order_by('-is_current', '-start_date')
        
        skill_list = profile.skills.all().order_by('skill_type', 'name')
        
        # Get achievements and alumni information
        alumni = None
        try:
            alumni = profile.user.alumni
            achievements = alumni.achievements_list.all().order_by('-date_achieved')

            # Get unified professional experience with current position first
            unified_experience = ProfessionalExperience.get_unified_experience(alumni)
        except Alumni.DoesNotExist:
            achievements = []
            unified_experience = experience_list
        
        # Check if user is a mentor
        is_mentor = Mentor.objects.filter(user=profile.user).exists()
        
        # Check if user has a pending mentor application
        has_pending_application = False
        try:
            if profile.user.mentor_application.status == 'PENDING':
                has_pending_application = True
        except (MentorApplication.DoesNotExist, AttributeError):
            pass
        
        context = {
            'profile': profile,
            'alumni': alumni,  # Add alumni information to context
            'education_list': education_list,
            'experience_list': experience_list,
            'skill_list': skill_list,
            'career_path': career_path_items,
            'work_experience': work_experience_items,
            'achievements': achievements,
            'unified_experience': unified_experience,
            'is_own_profile': request.user == profile.user,
            'is_mentor': is_mentor,
            'has_pending_application': has_pending_application,
        }
        
        return render(request, 'accounts/profile_detail.html', context)
    except Exception as e:
        logger.error(f'Error in profile_detail view: {str(e)}')
        messages.error(request, 'There was an error loading your profile. Please try again.')
        # Instead of redirecting to home (which could cause a loop),
        # render a simple error page or redirect to a safe page
        return render(request, 'accounts/profile_error.html', {
            'error_message': 'Unable to load profile information.',
            'user': request.user
        })

@login_required
def profile_update(request):
    if request.method == 'POST':
        try:
            user_form = UserUpdateForm(request.POST, instance=request.user)
            profile_form = ProfileUpdateForm(
                request.POST, 
                request.FILES, 
                instance=request.user.profile
            )
            education_formset = EducationFormSet(
                request.POST, 
                instance=request.user.profile,
                prefix='education'
            )
            experience_formset = ExperienceFormSet(
                request.POST, 
                instance=request.user.profile,
                prefix='experience'
            )
            skill_formset = SkillFormSet(
                request.POST, 
                instance=request.user.profile,
                prefix='skill'
            )
            
            # Document forms
            transcript_form = TranscriptUploadForm(
                request.POST, 
                request.FILES, 
                prefix='transcript',
                instance=Document.objects.filter(profile=request.user.profile, document_type='TRANSCRIPT').first()
            )
            certificate_form = CertificateUploadForm(
                request.POST, 
                request.FILES, 
                prefix='certificate',
                instance=Document.objects.filter(profile=request.user.profile, document_type='CERTIFICATE').first()
            )
            diploma_form = DiplomaUploadForm(
                request.POST, 
                request.FILES, 
                prefix='diploma',
                instance=Document.objects.filter(profile=request.user.profile, document_type='DIPLOMA').first()
            )
            resume_form = ResumeUploadForm(
                request.POST, 
                request.FILES, 
                prefix='resume',
                instance=Document.objects.filter(profile=request.user.profile, document_type='RESUME').first()
            )

            forms_valid = all([
                user_form.is_valid(),
                profile_form.is_valid(),
                education_formset.is_valid(),
                experience_formset.is_valid(),
                skill_formset.is_valid()
            ])

            if forms_valid:
                try:
                    with transaction.atomic():
                        user_form.save()
                        profile = profile_form.save()
                        
                        # Handle avatar removal
                        if request.POST.get('remove_avatar') == 'true':
                            if profile.avatar:
                                import os
                                if os.path.exists(profile.avatar.path):
                                    os.remove(profile.avatar.path)
                                profile.avatar = None
                                profile.save()
                        
                        # Save formsets
                        education_formset.save()
                        experience_formset.save()
                        skill_formset.save()
                        
                        # Create or update current experience record if current position and employer are provided
                        current_position = profile_form.cleaned_data.get('current_position')
                        current_employer = profile_form.cleaned_data.get('current_employer')
                        
                        if current_position and current_employer:
                            # Check if there's already a current experience
                            current_exp = Experience.objects.filter(profile=profile, is_current=True).first()
                            
                            if current_exp:
                                # Update existing current experience
                                current_exp.position = current_position
                                current_exp.company = current_employer
                                current_exp.save()
                            else:
                                # Create new current experience
                                import datetime
                                Experience.objects.create(
                                    profile=profile,
                                    position=current_position,
                                    company=current_employer,
                                    location=profile.city or '',
                                    start_date=datetime.date.today(),
                                    is_current=True,
                                    career_significance='REGULAR'
                                )

                        # Update Alumni model
                        try:
                            alumni = request.user.alumni
                            alumni.phone_number = profile.phone_number
                            alumni.address = profile.address
                            alumni.city = profile.city
                            alumni.province = profile.state
                            alumni.country = profile.country
                            alumni.linkedin_profile = profile.linkedin_profile
                            alumni.date_of_birth = profile.birth_date
                            alumni.gender = profile.gender
                            alumni.save()
                        except Alumni.DoesNotExist:
                            pass

                        # Handle document uploads
                        for form in [transcript_form, certificate_form, diploma_form, resume_form]:
                            if form.is_valid() and form.has_changed():
                                if form.cleaned_data.get('file'):
                                    # Get file information before saving
                                    uploaded_file = form.cleaned_data.get('file')
                                    file_size = uploaded_file.size if uploaded_file else 0
                                    file_name = uploaded_file.name if uploaded_file else None
                                    
                                    # Save to Profile Document
                                    doc = form.save(commit=False)
                                    doc.profile = request.user.profile
                                    doc.save()

                                    # Log document upload
                                    logger.info(
                                        f"Document uploaded: Document ID={doc.id}, Type={doc.document_type}, File={file_name}, Size={file_size} bytes",
                                        extra={
                                            'document_id': doc.id,
                                            'document_title': doc.title,
                                            'document_type': doc.document_type,
                                            'file_name': file_name,
                                            'file_size': file_size,
                                            'user_id': request.user.id,
                                            'profile_id': request.user.profile.id,
                                            'action': 'document_upload'
                                        }
                                    )

                                    # Map document types between Profile and Alumni models
                                    document_type_mapping = {
                                        'TRANSCRIPT': 'TOR',
                                        'CERTIFICATE': 'CERT',
                                        'DIPLOMA': 'DIPLOMA',
                                        'RESUME': 'RESUME',
                                        'OTHER': 'OTHER'
                                    }

                                    # Save to Alumni Document
                                    try:
                                        alumni = request.user.alumni
                                        AlumniDocument.objects.create(
                                            alumni=alumni,
                                            title=doc.title,
                                            document_type=document_type_mapping.get(doc.document_type, 'OTHER'),
                                            file=doc.file,
                                            description='',  # Document model doesn't have description, so use empty string
                                            is_verified=False
                                        )
                                    except Alumni.DoesNotExist:
                                        pass
                                    except Exception as e:
                                        logger.error(
                                            f"Error creating AlumniDocument: {str(e)}",
                                            extra={
                                                'document_id': doc.id,
                                                'document_type': doc.document_type,
                                                'user_id': request.user.id,
                                                'error_type': type(e).__name__
                                            },
                                            exc_info=True
                                        )

                    # Log profile update success
                    changes = []
                    if user_form.has_changed():
                        changes.extend([f'user.{field}' for field in user_form.changed_data])
                    if profile_form.has_changed():
                        changes.extend([f'profile.{field}' for field in profile_form.changed_data])
                    
                    logger.info(
                        f"Profile updated successfully: User ID={request.user.id}",
                        extra={
                            'user_id': request.user.id,
                            'user_email': request.user.email,
                            'changes': changes if changes else 'No changes detected',
                            'education_count': education_formset.total_form_count(),
                            'experience_count': experience_formset.total_form_count(),
                            'skill_count': skill_formset.total_form_count(),
                            'action': 'profile_update'
                        }
                    )
                    
                    return JsonResponse({'status': 'success'})

                except Exception as e:
                    logger.error(
                        f"Error saving profile: {str(e)}",
                        extra={
                            'user_id': request.user.id,
                            'error_type': type(e).__name__
                        },
                        exc_info=True
                    )
                    return JsonResponse({
                        'status': 'error', 
                        'message': f'An error occurred while saving your profile: {str(e)}'
                    }, status=500)
            else:
                errors = {}
                # Handle form errors
                for form_name, form in [
                    ('user', user_form),
                    ('profile', profile_form)
                ]:
                    if not form.is_valid():
                        errors[form_name] = form.errors

                # Handle formset errors
                for formset_name, formset in [
                    ('education', education_formset),
                    ('experience', experience_formset),
                    ('skill', skill_formset)
                ]:
                    if not formset.is_valid():
                        formset_errors = []
                        for form in formset:
                            if form.errors:
                                formset_errors.append(form.errors)
                        if formset.non_form_errors():
                            formset_errors.append(formset.non_form_errors())
                        if formset_errors:
                            errors[formset_name] = formset_errors

                return JsonResponse({
                    'status': 'error',
                    'errors': errors
                }, status=400)
                
        except Exception as e:
            logger.error(f"Error processing profile update request: {str(e)}")
            return JsonResponse({
                'status': 'error', 
                'message': f'An error occurred while processing your request: {str(e)}'
            }, status=500)

    else:  # GET request
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
        education_formset = EducationFormSet(
            instance=request.user.profile, 
            prefix='education'
        )
        experience_formset = ExperienceFormSet(
            instance=request.user.profile, 
            prefix='experience'
        )
        skill_formset = SkillFormSet(
            instance=request.user.profile, 
            prefix='skill'
        )
        
        # Initialize document forms with existing instances
        transcript_form = TranscriptUploadForm(
            prefix='transcript',
            instance=Document.objects.filter(profile=request.user.profile, document_type='TRANSCRIPT').first()
        )
        certificate_form = CertificateUploadForm(
            prefix='certificate',
            instance=Document.objects.filter(profile=request.user.profile, document_type='CERTIFICATE').first()
        )
        diploma_form = DiplomaUploadForm(
            prefix='diploma',
            instance=Document.objects.filter(profile=request.user.profile, document_type='DIPLOMA').first()
        )
        resume_form = ResumeUploadForm(
            prefix='resume',
            instance=Document.objects.filter(profile=request.user.profile, document_type='RESUME').first()
        )

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'education_formset': education_formset,
        'experience_formset': experience_formset,
        'skill_formset': skill_formset,
        'transcript_form': transcript_form,
        'certificate_form': certificate_form,
        'diploma_form': diploma_form,
        'resume_form': resume_form,
    }
    return render(request, 'accounts/profile_update.html', context)

@login_required
def document_delete(request, pk):
    try:
        document = get_object_or_404(Document, pk=pk, profile=request.user.profile)
        document_title = document.title
        document_type = document.document_type
        
        # Log document deletion
        logger.info(
            f"Document deleted: Document ID={document.id}, Type={document_type}, Title={document_title}",
            extra={
                'document_id': document.id,
                'document_title': document_title,
                'document_type': document_type,
                'user_id': request.user.id,
                'profile_id': request.user.profile.id
            }
        )
        
        document.delete()
        messages.success(request, f'🗑️ Document "{document_title}" has been deleted successfully!')
        return redirect('accounts:profile_detail')
    except Exception as e:
        logger.error(
            f"Error deleting document: {str(e)}",
            extra={
                'document_id': pk,
                'user_id': request.user.id,
                'error_type': type(e).__name__
            },
            exc_info=True
        )
        messages.error(request, f'❌ Failed to delete document: {str(e)}')
        return redirect('accounts:profile_detail')

User = get_user_model()

@login_required
def search_users_api(request):
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse([], safe=False)
    
    users = User.objects.filter(
        Q(first_name__icontains=query) | 
        Q(last_name__icontains=query) |
        Q(email__icontains=query)
    ).exclude(id=request.user.id)[:10]
    
    data = [{
        'id': user.id,
        'username': user.username,
        'full_name': user.get_full_name(),
        'avatar_url': user.profile.avatar.url if hasattr(user, 'profile') and user.profile.avatar else '/static/images/default-avatar.png'
    } for user in users]
    
    return JsonResponse(data, safe=False)

@login_required
def search_connected_users_api(request):
    """Search only connected users for messaging"""
    from connections.models import Connection
    
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse([], safe=False)
    
    # Get connected users
    connected_users = Connection.get_user_connections(request.user, status='ACCEPTED')
    
    # Filter connected users by search query
    filtered_users = []
    for user in connected_users:
        if (query.lower() in user.first_name.lower() or 
            query.lower() in user.last_name.lower() or 
            query.lower() in user.get_full_name().lower() or
            query.lower() in user.username.lower()):
            filtered_users.append(user)
    
    # Limit to 10 results
    filtered_users = filtered_users[:10]
    
    data = [{
        'id': user.id,
        'username': user.username,
        'full_name': user.get_full_name(),
        'avatar_url': user.profile.avatar.url if hasattr(user, 'profile') and user.profile.avatar else '/static/images/default-avatar.png'
    } for user in filtered_users]
    
    return JsonResponse(data, safe=False)

@login_required
def user_detail_api(request, user_id):
    user = get_object_or_404(User, id=user_id)
    return JsonResponse({
        'id': user.id,
        'username': user.username,
        'full_name': user.get_full_name(),
        'avatar_url': user.profile.avatar.url if hasattr(user, 'profile') and user.profile.avatar else '/static/images/default-avatar.png'
    })

@login_required
def update_personal_info(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'success'})
            return redirect('accounts:profile_detail')
        else:
            errors = {**user_form.errors, **profile_form.errors}
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'errors': errors}, status=400)
    
    if request.GET.get('form_only'):
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
        return render(request, 'accounts/forms/personal_info_form.html', {
            'user_form': user_form,
            'profile_form': profile_form
        })
    
    return redirect('accounts:profile_detail')

@login_required
def update_skills(request):
    if request.method == 'POST':
        form = SkillForm(request.POST)
        if form.is_valid():
            try:
                skill = form.save(commit=False)
                skill.profile = request.user.profile
                skill.save()
                messages.success(request, f'✅ Skill "{skill.name}" has been added successfully!')
                return redirect('accounts:profile_detail')
            except Exception as e:
                messages.error(request, f'❌ Failed to add skill: {str(e)}')
                return redirect('accounts:profile_detail')
        else:
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")
            messages.error(request, f'❌ Please correct the following errors: {", ".join(error_messages)}')
            return redirect('accounts:profile_detail')
    else:
        form = SkillForm()
        if request.GET.get('form_only'):
            return render(request, 'accounts/forms/skill_form.html', {'form': form})
        return render(request, 'accounts/update_skills.html', {'form': form})

@login_required
def update_education(request):
    if request.method == 'POST':
        form = EducationForm(request.POST)
        if form.is_valid():
            try:
                education = form.save(commit=False)
                education.profile = request.user.profile
                education.save()
                messages.success(request, f'🎓 Education record for "{education.program}" has been added successfully!')
                return redirect('accounts:profile_detail')
            except Exception as e:
                messages.error(request, f'❌ Failed to add education record: {str(e)}')
                return redirect('accounts:profile_detail')
        else:
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")
            messages.error(request, f'❌ Please correct the following errors: {", ".join(error_messages)}')
            return redirect('accounts:profile_detail')
    else:
        form = EducationForm()
        if request.GET.get('form_only'):
            return render(request, 'accounts/forms/education_form.html', {'form': form})
        return render(request, 'accounts/update_education.html', {'form': form})

@login_required
def update_experience(request):
    if request.method == 'POST':
        form = ExperienceForm(request.POST)
        if form.is_valid():
            try:
                experience = form.save(commit=False)
                experience.profile = request.user.profile
                experience.save()
                messages.success(request, f'💼 Work experience at "{experience.company}" has been added successfully!')
                return redirect('accounts:profile_detail')
            except Exception as e:
                messages.error(request, f'❌ Failed to add work experience: {str(e)}')
                return redirect('accounts:profile_detail')
        else:
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")
            messages.error(request, f'❌ Please correct the following errors: {", ".join(error_messages)}')
            return redirect('accounts:profile_detail')
    else:
        form = ExperienceForm()
        if request.GET.get('form_only'):
            return render(request, 'accounts/forms/experience_form.html', {'form': form})
        return render(request, 'accounts/update_experience.html', {'form': form})

@login_required
def update_documents(request):
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                document = form.save(commit=False)
                document.profile = request.user.profile
                document.save()
                messages.success(request, f'📄 Document "{document.title}" has been uploaded successfully!')
                return redirect('accounts:profile_detail')
            except Exception as e:
                messages.error(request, f'❌ Failed to upload document: {str(e)}')
                return redirect('accounts:profile_detail')
        else:
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")
            messages.error(request, f'❌ Please correct the following errors: {", ".join(error_messages)}')
            return redirect('accounts:profile_detail')
    else:
        form = DocumentUploadForm()
        if request.GET.get('form_only'):
            return render(request, 'accounts/forms/document_form.html', {'form': form})
        return render(request, 'accounts/update_documents.html', {'form': form})

@login_required
def edit_personal_info(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(
            request.POST, 
            request.FILES, 
            instance=request.user.profile
        )
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile = profile_form.save()
            
            # Handle avatar removal
            if request.POST.get('remove_avatar') == 'on':
                if profile.avatar:
                    import os
                    if os.path.exists(profile.avatar.path):
                        os.remove(profile.avatar.path)
                    profile.avatar = None
                    profile.save()
            
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('accounts:profile_detail')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
    
    return render(request, 'accounts/edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': request.user.profile
    })

@login_required
def edit_education(request, pk):
    education = get_object_or_404(Education, pk=pk, profile=request.user.profile)
    
    if request.method == 'POST':
        form = EducationForm(request.POST, instance=education)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f'🎓 Education record for "{education.program}" has been updated successfully!')
                return redirect('accounts:profile_detail')
            except Exception as e:
                messages.error(request, f'❌ Failed to update education record: {str(e)}')
                return redirect('accounts:profile_detail')
        else:
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")
            messages.error(request, f'❌ Please correct the following errors: {", ".join(error_messages)}')
            return redirect('accounts:profile_detail')
    
    if request.GET.get('form_only'):
        form = EducationForm(instance=education)
        return render(request, 'accounts/forms/education_form.html', {'form': form})
    
    return redirect('accounts:profile_detail')

@login_required
def delete_education(request, pk):
    if request.method == 'POST':
        try:
            education = get_object_or_404(Education, pk=pk, profile=request.user.profile)
            education_program = education.program
            education.delete()
            messages.success(request, f'🗑️ Education record for "{education_program}" has been deleted successfully!')
            return redirect('accounts:profile_detail')
        except Exception as e:
            messages.error(request, f'❌ Failed to delete education record: {str(e)}')
            return redirect('accounts:profile_detail')

@login_required
def manage_members(request, group_id):
    group = get_object_or_404(AlumniGroup, id=group_id)
    
    # Check if user has permission to manage the group
    membership = GroupMembership.objects.filter(
        group=group,
        user=request.user,
        status='active'
    ).first()
    
    # Only allow staff or group admins to manage members
    if not (request.user.is_staff or (membership and membership.role == 'ADMIN')):
        return HttpResponseForbidden("You don't have permission to manage members.")
    
    active_members = GroupMembership.objects.filter(
        group=group, 
        status='active'
    ).select_related('user')
    
    pending_members = GroupMembership.objects.filter(
        group=group, 
        status='pending'
    ).select_related('user')
    
    removed_members = GroupMembership.objects.filter(
        group=group, 
        status='removed'
    ).select_related('user')
    
    context = {
        'group': group,
        'active_members': active_members,
        'pending_members': pending_members,
        'removed_members': removed_members,
    }
    return render(request, 'accounts/manage_members.html', context)

@login_required
@require_POST
def update_member_status(request, membership_id):
    membership = get_object_or_404(GroupMembership, id=membership_id)
    
    # Check permissions
    user_membership = GroupMembership.objects.filter(
        group=membership.group,
        user=request.user,
        status='active'
    ).first()
    
    if not (request.user.is_staff or (user_membership and user_membership.role == 'ADMIN')):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    action = request.POST.get('action')
    
    if action == 'accept':
        membership.status = 'active'
    elif action == 'remove':
        membership.status = 'removed'
    else:
        return JsonResponse({'error': 'Invalid action'}, status=400)
    
    membership.save()
    
    return JsonResponse({
        'status': 'success',
        'new_status': membership.status
    })

@login_required
def view_security_answer(request, membership_id):
    membership = get_object_or_404(GroupMembership, id=membership_id)
    
    # Check permissions
    user_membership = GroupMembership.objects.filter(
        group=membership.group,
        user=request.user,
        status='active'
    ).first()
    
    if not (request.user.is_staff or (user_membership and user_membership.role == 'ADMIN')):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    return JsonResponse({
        'answer': membership.security_answer
    })

@login_required
@require_POST
def add_career_path(request):
    try:
        user = request.user
        data = request.POST.dict()
        data['is_current'] = 'is_current' in data
        
        # Create experience with career significance
        experience = Experience.objects.create(
            profile=user.profile,
            company=data['company'],
            position=data['position'],
            start_date=data['start_date'],
            end_date=data.get('end_date') if not data['is_current'] else None,
            is_current=data['is_current'],
            description=data.get('description', ''),
            achievements=data.get('achievements', ''),
            career_significance=data.get('career_significance', 'REGULAR'),  # Updated to use career_significance
            salary_range=data.get('salary_range', ''),
            location=data.get('location', ''),
            skills_gained=data.get('skills_gained', '')
        )
        
        messages.success(request, f'🚀 Career path at "{experience.company}" has been added successfully!')
        return redirect('accounts:profile_detail')
    except Exception as e:
        messages.error(request, f'❌ Failed to add career path: {str(e)}')
        return redirect('accounts:profile_detail')

@login_required
@require_POST
def edit_career_path(request, pk):
    try:
        experience = get_object_or_404(Experience, pk=pk, profile=request.user.profile)
        data = request.POST.dict()
        data['is_current'] = 'is_current' in data
        
        # Update the experience
        for field, value in data.items():
            if field != 'csrfmiddlewaretoken':
                if field == 'end_date' and data['is_current']:
                    value = None
                # Map fields if needed
                if field == 'promotion_type':
                    field = 'career_significance'
                setattr(experience, field, value)
        
        experience.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Career path updated successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@login_required
@require_POST
def delete_career_path(request, pk):
    try:
        experience = get_object_or_404(Experience, pk=pk, profile=request.user.profile)
        experience.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Career path deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@login_required
@require_POST
def add_achievement(request):
    try:
        alumni = request.user.alumni
        data = request.POST.dict()
        file = request.FILES.get('attachment')
        
        # Create the achievement
        achievement = Achievement.objects.create(
            alumni=alumni,
            title=data['title'],
            achievement_type=data['achievement_type'],
            date_achieved=data['date_achieved'],
            description=data.get('description', ''),
            issuer=data.get('issuer', ''),
            url=data.get('url', ''),
            attachment=file
        )
        
        # Log achievement creation
        logger.info(
            f"Achievement added: Achievement ID={achievement.id}, Type={achievement.achievement_type}, Title={achievement.title}",
            extra={
                'achievement_id': achievement.id,
                'achievement_title': achievement.title,
                'achievement_type': achievement.achievement_type,
                'achievement_date': str(achievement.date_achieved),
                'alumni_id': alumni.id,
                'user_id': request.user.id,
                'has_attachment': bool(file)
            }
        )
        
        messages.success(request, f'🏆 Achievement "{achievement.title}" has been added successfully!')
        return redirect('accounts:profile_detail')
    except Exception as e:
        logger.error(
            f"Error adding achievement: {str(e)}",
            extra={
                'alumni_id': request.user.alumni.id if hasattr(request.user, 'alumni') else None,
                'user_id': request.user.id,
                'error_type': type(e).__name__
            },
            exc_info=True
        )
        messages.error(request, f'❌ Failed to add achievement: {str(e)}')
        return redirect('accounts:profile_detail')

@login_required
@require_POST
def edit_achievement(request, pk):
    try:
        achievement = get_object_or_404(Achievement, pk=pk, alumni=request.user.alumni)
        data = request.POST.dict()
        file = request.FILES.get('attachment')
        
        # Update the achievement
        for field, value in data.items():
            if field != 'csrfmiddlewaretoken':
                setattr(achievement, field, value)
        
        if file:
            achievement.attachment = file
        
        achievement.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Achievement updated successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@login_required
@require_POST
def delete_achievement(request, pk):
    try:
        achievement = get_object_or_404(Achievement, pk=pk, alumni=request.user.alumni)
        achievement.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Achievement deleted successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.profile.user == request.user

class SkillViewSet(viewsets.ModelViewSet):
    serializer_class = SkillSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'skill_type']

    def get_queryset(self):
        return Skill.objects.filter(profile__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(profile=self.request.user.profile)

class ProfileSkillsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProfileSkillsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Profile.objects.filter(
            Q(user=self.request.user) | Q(is_public=True)
        ).prefetch_related('skills')

class SkillMatchViewSet(viewsets.ModelViewSet):
    serializer_class = SkillMatchSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SkillMatch.objects.filter(profile__user=self.request.user)

    @action(detail=False, methods=['post'])
    def calculate_match(self, request):
        serializer = SkillMatchCalculationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        job = serializer.validated_data['job']
        profile = serializer.validated_data['profile']

        # Get required skills from job posting
        required_skills = set(
            skill.strip().lower()
            for skill in job.skills_required.split(',')
            if skill.strip()
        )

        # Get user's skills
        user_skills = {
            skill.name.lower(): {
                'proficiency': skill.proficiency_level,
                'years': skill.years_of_experience,
                'is_primary': skill.is_primary
            }
            for skill in profile.skills.all()
        }

        # Calculate matches
        matched_skills = {}
        missing_skills = []
        total_weight = 0
        match_score = 0

        for skill in required_skills:
            if skill in user_skills:
                weight = 1.0
                if user_skills[skill]['is_primary']:
                    weight *= 1.2
                weight *= min(user_skills[skill]['years'] * 0.1 + 1, 2.0)
                weight *= user_skills[skill]['proficiency'] * 0.2

                matched_skills[skill] = {
                    'weight': weight,
                    'proficiency': user_skills[skill]['proficiency'],
                    'years': user_skills[skill]['years']
                }
                match_score += weight
                total_weight += 1
            else:
                missing_skills.append(skill)

        # Normalize score to percentage
        if total_weight > 0:
            match_score = (match_score / total_weight) * 100
        else:
            match_score = 0

        # Create or update SkillMatch
        skill_match, created = SkillMatch.objects.update_or_create(
            job=job,
            profile=profile,
            defaults={
                'match_score': match_score,
                'matched_skills': matched_skills,
                'missing_skills': missing_skills,
                'is_notified': False,
                'is_viewed': False
            }
        )

        return Response(SkillMatchSerializer(skill_match).data)

    @action(detail=True, methods=['post'])
    def mark_viewed(self, request, pk=None):
        match = self.get_object()
        match.is_viewed = True
        match.save()
        return Response(SkillMatchSerializer(match).data)

    @action(detail=True, methods=['post'])
    def mark_applied(self, request, pk=None):
        match = self.get_object()
        match.is_applied = True
        match.save()
        return Response(SkillMatchSerializer(match).data)

@login_required
def skill_matching(request):
    """
    View for skill matching and job recommendations
    """
    return render(request, 'accounts/skill_matching.html')

@login_required
def apply_mentor(request):
    """View for submitting mentor applications"""
    # Check if user already has a pending or approved application
    existing_application = None
    try:
        existing_application = request.user.mentor_application
        if existing_application.status == 'PENDING':
            messages.info(request, 'You already have a pending mentor application.')
            return redirect('accounts:mentor_application_status')
        elif existing_application.status == 'APPROVED':
            messages.info(request, 'You are already an approved mentor.')
            return redirect('mentorship:mentor_dashboard')
    except MentorApplication.DoesNotExist:
        pass

    if request.method == 'POST':
        form = MentorApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # If user has a rejected application, update it instead of creating new one
                if existing_application and existing_application.status == 'REJECTED':
                    # Update existing rejected application
                    # Get cleaned data from form
                    existing_application.expertise_areas = form.cleaned_data['expertise_areas']
                    existing_application.years_of_experience = form.cleaned_data['years_of_experience']
                    existing_application.competency_summary = form.cleaned_data['competency_summary']
                    
                    # Update file fields if new files were uploaded
                    if form.cleaned_data.get('certifications'):
                        existing_application.certifications = form.cleaned_data['certifications']
                    if form.cleaned_data.get('training_documents'):
                        existing_application.training_documents = form.cleaned_data['training_documents']
                    
                    # Reset status and review fields
                    existing_application.status = 'PENDING'
                    existing_application.review_date = None
                    existing_application.reviewed_by = None
                    existing_application.review_notes = ''
                    # Note: application_date remains unchanged (auto_now_add)
                    
                    application = existing_application
                    application.save()
                    
                    # Log mentor application resubmission
                    logger.info(
                        f"Mentor application resubmitted: Application ID={application.id}, User ID={request.user.id}",
                        extra={
                            'application_id': application.id,
                            'user_id': request.user.id,
                            'user_email': request.user.email,
                            'expertise_areas': application.expertise_areas,
                            'action': 'mentor_application_resubmit',
                            'previous_status': 'REJECTED'
                        }
                    )
                    
                    messages.success(request, 'Your mentor application has been resubmitted successfully. We will review it shortly.')
                else:
                    # Create new application
                    application = form.save(commit=False)
                    application.user = request.user
                    application.save()
                    
                    # Log mentor application submission
                    logger.info(
                        f"Mentor application submitted: Application ID={application.id}, User ID={request.user.id}",
                        extra={
                            'application_id': application.id,
                            'user_id': request.user.id,
                            'user_email': request.user.email,
                            'expertise_areas': application.expertise_areas,
                            'action': 'mentor_application_submit'
                        }
                    )
                    
                    messages.success(request, 'Your mentor application has been submitted successfully. We will review it shortly.')
                
                return redirect('accounts:mentor_application_status')
            except Exception as e:
                logger.error(
                    f"Error submitting mentor application: {str(e)}",
                    extra={
                        'user_id': request.user.id,
                        'error_type': type(e).__name__
                    },
                    exc_info=True
                )
                messages.error(request, f'An error occurred: {str(e)}')
                raise
    else:
        # Pre-fill form with existing rejected application data if available
        if existing_application and existing_application.status == 'REJECTED':
            form = MentorApplicationForm(instance=existing_application)
        else:
            form = MentorApplicationForm()
    
    return render(request, 'accounts/mentor_application_form.html', {'form': form})

@login_required
def mentor_application_status(request):
    """View for checking mentor application status"""
    try:
        application = request.user.mentor_application
        return render(request, 'accounts/mentor_application_status.html', {
            'application': application
        })
    except MentorApplication.DoesNotExist:
        messages.error(request, 'No mentor application found.')
        return redirect('accounts:apply_mentor')

@user_passes_test(lambda u: u.is_staff)
@paginate(per_page=10)
def review_mentor_applications(request):
    """Admin view for reviewing mentor applications"""
    applications = MentorApplication.objects.filter(status='PENDING').select_related('user')
    return render(request, 'accounts/review_mentor_applications.html', {
        'applications': applications
    })

@user_passes_test(lambda u: u.is_staff)
def review_mentor_application(request, application_id):
    """Admin view for reviewing a specific mentor application"""
    try:
        application = MentorApplication.objects.get(id=application_id)
    except MentorApplication.DoesNotExist:
        messages.error(request, 'Application not found.')
        return redirect('accounts:review_mentor_applications')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        review_notes = request.POST.get('review_notes', '')
        
        application.review_notes = review_notes
        application.review_date = timezone.now()
        application.reviewed_by = request.user
        
        try:
            if action == 'approve':
                application.status = 'APPROVED'
                # Create or update Mentor profile
                mentor, created = Mentor.objects.get_or_create(user=application.user)
                mentor.expertise_areas = application.expertise_areas
                mentor.is_verified = True
                mentor.verification_date = timezone.now()
                mentor.verified_by = request.user
                mentor.save()
                
                # Log application approval
                logger.info(
                    f"Mentor application approved: Application ID={application.id}, User ID={application.user.id}, Mentor created={created}",
                    extra={
                        'application_id': application.id,
                        'user_id': application.user.id,
                        'reviewer_id': request.user.id,
                        'decision': 'approve',
                        'mentor_created': created,
                        'action': 'mentor_application_review'
                    }
                )
                
                messages.success(request, f'Mentor application for {application.user.get_full_name()} has been approved.')
            elif action == 'reject':
                application.status = 'REJECTED'
                
                # Log application rejection
                logger.info(
                    f"Mentor application rejected: Application ID={application.id}, User ID={application.user.id}",
                    extra={
                        'application_id': application.id,
                        'user_id': application.user.id,
                        'reviewer_id': request.user.id,
                        'decision': 'reject',
                        'review_notes': review_notes[:200],  # Truncate for logging
                        'action': 'mentor_application_review'
                    }
                )
                
                messages.success(request, f'Mentor application for {application.user.get_full_name()} has been rejected.')
            
            application.save()
            
            # Send notification to user
            # TODO: Implement notification system
            
            # Handle AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': f'Mentor application for {application.user.get_full_name()} has been {"approved" if action == "approve" else "rejected"}.'
                })
            
            return redirect('accounts:review_mentor_applications')
        except Exception as e:
            logger.error(
                f"Error reviewing mentor application: {str(e)}",
                extra={
                    'application_id': application.id,
                    'reviewer_id': request.user.id,
                    'action': action,
                    'error_type': type(e).__name__
                },
                exc_info=True
            )
            # Handle AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': f'An error occurred: {str(e)}'
                }, status=500)
            
            messages.error(request, f'An error occurred: {str(e)}')
            raise
    
    # Handle GET request
    return render(request, 'accounts/review_mentor_applications.html', {
        'applications': [application]
    })

@user_passes_test(lambda u: u.is_staff)
def mentor_application_detail_modal(request, application_id):
    """
    Return mentor application detail content for modal display.
    """
    try:
        application = get_object_or_404(MentorApplication, id=application_id)
        logger.info(f"Mentor application detail modal accessed for ID: {application_id}, User: {application.user.get_full_name()}")

        return render(request, 'accounts/partials/mentor_application_detail_modal.html', {
            'application': application
        })
    except Exception as e:
        logger.error(
            f"Error loading mentor application detail modal: {str(e)}",
            extra={
                'application_id': application_id,
                'error_type': type(e).__name__
            },
            exc_info=True
        )
        return render(request, 'accounts/partials/mentor_application_detail_modal.html', {
            'error': f'Error loading application details: {str(e)}'
        })

@user_passes_test(lambda u: u.is_staff)
def mentor_reactivation_request_detail_modal(request, request_id):
    """
    Return mentor reactivation request detail content for modal display.
    """
    try:
        reactivation_request = get_object_or_404(
            MentorReactivationRequest.objects.select_related(
                'mentor', 'mentor__user', 'mentor__user__profile', 
                'requested_by', 'reviewed_by'
            ),
            id=request_id
        )
        logger.info(
            f"Mentor reactivation request detail modal accessed for ID: {request_id}, "
            f"Mentor: {reactivation_request.mentor.user.get_full_name()}"
        )

        return render(request, 'accounts/partials/mentor_reactivation_request_detail_modal.html', {
            'reactivation_request': reactivation_request
        })
    except Exception as e:
        logger.error(
            f"Error loading mentor reactivation request detail modal: {str(e)}",
            extra={
                'request_id': request_id,
                'error_type': type(e).__name__
            },
            exc_info=True
        )
        return render(request, 'accounts/partials/mentor_reactivation_request_detail_modal.html', {
            'error': f'Error loading reactivation request details: {str(e)}'
        })

@login_required
def admin_mentor_list(request):
    """
    Custom view to display a list of mentors for administrators
    """
    # Check if the user is a superuser
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('core:home')
        
    # Get all mentors
    mentors = Mentor.objects.all().select_related('user')
    
    # Add sorting options
    sort_by = request.GET.get('sort', 'name')
    if sort_by == 'name':
        mentors = mentors.order_by('user__first_name', 'user__last_name')
    elif sort_by == 'availability':
        mentors = mentors.order_by('availability_status')
    elif sort_by == 'mentees':
        mentors = mentors.order_by('-current_mentees')
    elif sort_by == 'verification':
        mentors = mentors.order_by('-is_verified')
    else:
        mentors = mentors.order_by('user__first_name', 'user__last_name')
    
    # Get mentorship statistics
    total_mentors = mentors.count()
    active_mentors = mentors.filter(is_active=True, accepting_mentees=True).count()
    verified_mentors = mentors.filter(is_verified=True).count()
    total_mentees = sum(mentor.current_mentees for mentor in mentors)
    
    # Get pending applications count
    pending_applications = MentorApplication.objects.filter(status='PENDING').count()
    
    # Get pending reactivation requests count
    pending_reactivation_requests = MentorReactivationRequest.objects.filter(status='PENDING').count()
    
    context = {
        'mentors': mentors,
        'total_mentors': total_mentors,
        'active_mentors': active_mentors,
        'verified_mentors': verified_mentors,
        'total_mentees': total_mentees,
        'pending_applications': pending_applications,
        'pending_reactivation_requests': pending_reactivation_requests,
        'sort_by': sort_by,
    }
    return render(request, 'accounts/admin_mentor_list.html', context)

@user_passes_test(lambda u: u.is_staff)
@require_POST
def remove_mentor(request, mentor_id):
    """
    Remove a mentor (soft delete) with validation and audit logging.
    Prevents removal if mentor has active mentorships.
    """
    try:
        mentor = get_object_or_404(Mentor, id=mentor_id)
        
        # Check if mentor is already removed
        if not mentor.is_active:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'This mentor has already been disabled.'
                }, status=400)
            messages.error(request, 'This mentor has already been disabled.')
            return redirect('accounts:admin_mentor_list')
        
        # Check for active mentorships
        active_count = mentor.get_active_mentorships_count()
        if active_count > 0:
            error_message = f'Cannot disable mentor. They have {active_count} active mentorship(s). Please complete or cancel all active mentorships before disabling the mentor.'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': error_message,
                    'active_mentorships_count': active_count
                }, status=400)
            
            messages.error(request, error_message)
            return redirect('accounts:admin_mentor_list')
        
        # Require removal reason
        removal_reason = request.POST.get('removal_reason', '').strip()
        if not removal_reason:
            error_message = 'Disable reason is required.'
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': error_message
                }, status=400)
            
            messages.error(request, error_message)
            return redirect('accounts:admin_mentor_list')
        
        # Store old values for audit log
        old_values = {
            'is_active': mentor.is_active,
            'accepting_mentees': mentor.accepting_mentees,
            'availability_status': mentor.availability_status,
        }
        
        # Soft delete: set is_active=False and update related fields
        with transaction.atomic():
            mentor.is_active = False
            mentor.accepting_mentees = False
            mentor.availability_status = 'UNAVAILABLE'
            mentor.removal_reason = removal_reason
            mentor.removed_at = timezone.now()
            mentor.removed_by = request.user
            mentor.save()
            
            # Create audit log entry manually (since soft delete won't trigger DELETE signal)
            content_type = ContentType.objects.get_for_model(Mentor)
            
            # Get request info
            ip_address = None
            user_agent = None
            request_path = None
            if hasattr(request, 'META'):
                ip_address = request.META.get('REMOTE_ADDR')
                user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
                request_path = request.path[:500]
            
            # Create audit log
            audit_log = AuditLog.objects.create(
                content_type=content_type,
                object_id=mentor.id,
                action='UPDATE',  # Using UPDATE since we're soft deleting
                model_name='mentor',
                app_label='accounts',
                user=request.user,
                username=request.user.username,
                old_values=old_values,
                new_values={
                    'is_active': False,
                    'accepting_mentees': False,
                    'availability_status': 'UNAVAILABLE',
                    'removal_reason': removal_reason,
                    'removed_at': str(mentor.removed_at),
                    'removed_by': request.user.username,
                },
                changed_fields=['is_active', 'accepting_mentees', 'availability_status', 'removal_reason', 'removed_at', 'removed_by'],
                ip_address=ip_address,
                user_agent=user_agent,
                request_path=request_path,
                message=f"Mentor removed: {mentor.user.get_full_name()} - Reason: {removal_reason[:200]}",
                timestamp=timezone.now(),
            )
            
            # Log to Python logger
            logger.info(
                f"Mentor removed: Mentor ID={mentor.id}, User ID={mentor.user.id}, "
                f"Removed by={request.user.username}, Active mentorships={active_count}, Reason={removal_reason[:200]}",
                extra={
                    'mentor_id': mentor.id,
                    'user_id': mentor.user.id,
                    'removed_by': request.user.id,
                    'removed_by_username': request.user.username,
                    'active_mentorships_count': active_count,
                    'removal_reason': removal_reason[:200],
                    'action': 'mentor_removal',
                    'audit_log_id': audit_log.id,
                }
            )
            
            # Create notification for the mentor
            notification_message = f'Your mentorship status has been disabled by an administrator.'
            if removal_reason:
                notification_message += f'\n\nReason: {removal_reason[:500]}'
            
            Notification.create_notification(
                recipient=mentor.user,
                notification_type='mentorship_disabled',
                title='Your Mentorship Status Has Been Disabled',
                message=notification_message,
                sender=request.user,
                content_object=mentor,
                action_url=reverse('mentorship:mentor_dashboard')
            )
        
        success_message = f'Mentor "{mentor.user.get_full_name()}" has been successfully disabled.'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': success_message
            })
        
        messages.success(request, success_message)
        return redirect('accounts:admin_mentor_list')
        
    except Exception as e:
        logger.error(
            f"Error removing mentor: {str(e)}",
            extra={
                'mentor_id': mentor_id,
                'removed_by': request.user.id if request.user.is_authenticated else None,
                'error_type': type(e).__name__
            },
            exc_info=True
        )
        
        error_message = f'An error occurred while removing the mentor: {str(e)}'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': error_message
            }, status=500)
        
        messages.error(request, error_message)
        return redirect('accounts:admin_mentor_list')

@login_required
@require_POST
def send_reactivation_verification_code(request):
    """
    Send verification code to email for mentor reactivation request.
    """
    import json
    from .security import SecurityCodeManager, RateLimiter
    
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        reason = data.get('reason', '').strip()
        
        if not email:
            return JsonResponse({
                'success': False,
                'error': 'Email address is required.'
            }, status=400)
        
        # Check if user is a mentor
        try:
            mentor = request.user.mentor_profile
        except:
            return JsonResponse({
                'success': False,
                'error': 'You must be a mentor to request reactivation.'
            }, status=403)
        
        # Check if mentor is actually disabled
        if mentor.is_active:
            return JsonResponse({
                'success': False,
                'error': 'Your mentorship status is already active.'
            }, status=400)
        
        # Verify email matches mentor's email
        if email.lower() != request.user.email.lower():
            return JsonResponse({
                'success': False,
                'error': 'Email address must match your account email.'
            }, status=400)
        
        # Check rate limiting
        if RateLimiter.is_rate_limited(email, 'reactivation_attempt'):
            return JsonResponse({
                'success': False,
                'error': 'Too many attempts. Please try again later.'
            }, status=429)
        
        # Check for existing pending request
        existing_request = MentorReactivationRequest.objects.filter(
            mentor=mentor,
            status='PENDING'
        ).first()
        
        if existing_request:
            return JsonResponse({
                'success': False,
                'error': 'You already have a pending reactivation request. Please wait for admin review.'
            }, status=400)
        
        # Generate verification code
        code = SecurityCodeManager.generate_code()
        SecurityCodeManager.store_code(email, code, 'mentor_reactivation', expiry_minutes=15)
        
        # Send verification email
        from .email_utils import render_mentor_reactivation_verification_email
        from core.email_utils import send_email_with_provider
        from django.conf import settings
        
        user = request.user
        html_content = render_mentor_reactivation_verification_email(user, code)
        plain_message = f"""
Hello {user.get_full_name()}!

You have requested to reactivate your mentorship status. Please use the following verification code:

Verification Code: {code}

This code will expire in 15 minutes.

If you didn't request this reactivation, please ignore this email.

Best regards,
NORSU Alumni Network Team
        """
        
        success = send_email_with_provider(
            subject='NORSU Alumni - Mentor Reactivation Verification Code',
            message=plain_message,
            recipient_list=[email],
            from_email=settings.DEFAULT_FROM_EMAIL,
            html_message=html_content,
            fail_silently=False
        )
        
        if success:
            RateLimiter.record_attempt(email, 'reactivation_attempt')
            
            # Store email and reason in session for verification step
            request.session['reactivation_email'] = email
            request.session['reactivation_reason'] = reason
            
            logger.info(
                f"Reactivation verification code sent: Mentor ID={mentor.id}, User ID={request.user.id}, Email={email}",
                extra={
                    'mentor_id': mentor.id,
                    'user_id': request.user.id,
                    'email': email,
                    'action': 'send_reactivation_code'
                }
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Verification code sent to your email.'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Failed to send verification code. Please try again.'
            }, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid request data.'
        }, status=400)
    except Exception as e:
        logger.error(
            f"Error sending reactivation verification code: {str(e)}",
            extra={
                'user_id': request.user.id if request.user.is_authenticated else None,
                'error_type': type(e).__name__
            },
            exc_info=True
        )
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)

@login_required
@require_POST
def verify_reactivation_code(request):
    """
    Verify reactivation code and create reactivation request.
    """
    import json
    from .security import SecurityCodeManager
    
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        code = data.get('code', '').strip()
        reason = data.get('reason', '').strip()
        
        # Fallback to session data if reason not provided in request body
        if not reason and 'reactivation_reason' in request.session:
            reason = request.session.get('reactivation_reason', '').strip()
        
        if not email or not code:
            return JsonResponse({
                'success': False,
                'error': 'Email and verification code are required.'
            }, status=400)
        
        # Check if user is a mentor
        try:
            mentor = request.user.mentor_profile
        except:
            return JsonResponse({
                'success': False,
                'error': 'You must be a mentor to request reactivation.'
            }, status=403)
        
        # Check if mentor is actually disabled
        if mentor.is_active:
            return JsonResponse({
                'success': False,
                'error': 'Your mentorship status is already active.'
            }, status=400)
        
        # Verify email matches mentor's email
        if email.lower() != request.user.email.lower():
            return JsonResponse({
                'success': False,
                'error': 'Email address must match your account email.'
            }, status=400)
        
        # Verify code
        is_valid, message = SecurityCodeManager.verify_code(email, code, 'mentor_reactivation')
        
        if not is_valid:
            return JsonResponse({
                'success': False,
                'error': message
            }, status=400)
        
        # Check for existing pending request
        existing_request = MentorReactivationRequest.objects.filter(
            mentor=mentor,
            status='PENDING'
        ).first()
        
        if existing_request:
            return JsonResponse({
                'success': False,
                'error': 'You already have a pending reactivation request. Please wait for admin review.'
            }, status=400)
        
        # Create reactivation request
        with transaction.atomic():
            reactivation_request = MentorReactivationRequest.objects.create(
                mentor=mentor,
                requested_by=request.user,
                email=email,
                verification_code=code,
                is_verified=True,
                status='PENDING',
                request_reason=reason
            )
            
            # Create audit log
            content_type = ContentType.objects.get_for_model(MentorReactivationRequest)
            
            # Get request info
            ip_address = None
            user_agent = None
            request_path = None
            if hasattr(request, 'META'):
                ip_address = request.META.get('REMOTE_ADDR')
                user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
                request_path = request.path[:500]
            
            # Create audit log
            audit_log = AuditLog.objects.create(
                content_type=content_type,
                object_id=reactivation_request.id,
                action='CREATE',
                model_name='mentor_reactivation_request',
                app_label='accounts',
                user=request.user,
                username=request.user.username,
                old_values={},
                new_values={
                    'mentor_id': mentor.id,
                    'mentor_name': mentor.user.get_full_name(),
                    'email': email,
                    'status': 'PENDING',
                    'request_reason': reason[:200] if reason else None,
                },
                changed_fields=['mentor', 'requested_by', 'email', 'status', 'request_reason'],
                ip_address=ip_address,
                user_agent=user_agent,
                request_path=request_path,
                message=f"Mentor reactivation request created: {mentor.user.get_full_name()}",
                timestamp=timezone.now(),
            )
            
            # Log to Python logger
            logger.info(
                f"Mentor reactivation request created: Request ID={reactivation_request.id}, Mentor ID={mentor.id}, User ID={request.user.id}",
                extra={
                    'reactivation_request_id': reactivation_request.id,
                    'mentor_id': mentor.id,
                    'user_id': request.user.id,
                    'action': 'create_reactivation_request',
                    'audit_log_id': audit_log.id,
                }
            )
        
        # Clear session data
        if 'reactivation_email' in request.session:
            del request.session['reactivation_email']
        if 'reactivation_reason' in request.session:
            del request.session['reactivation_reason']
        
        return JsonResponse({
            'success': True,
            'message': 'Reactivation request submitted successfully. An admin will review it shortly.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid request data.'
        }, status=400)
    except Exception as e:
        logger.error(
            f"Error verifying reactivation code: {str(e)}",
            extra={
                'user_id': request.user.id if request.user.is_authenticated else None,
                'error_type': type(e).__name__
            },
            exc_info=True
        )
        return JsonResponse({
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }, status=500)

@user_passes_test(lambda u: u.is_staff)
@paginate(per_page=10)
def review_mentor_reactivation_requests(request):
    """
    Admin view for reviewing mentor reactivation requests.
    """
    requests = MentorReactivationRequest.objects.all().select_related('mentor', 'mentor__user', 'requested_by', 'reviewed_by').order_by('-requested_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status', '')
    if status_filter:
        requests = requests.filter(status=status_filter)
    
    context = {
        'requests': requests,
        'status_filter': status_filter,
        'total_pending': MentorReactivationRequest.objects.filter(status='PENDING').count(),
        'total_approved': MentorReactivationRequest.objects.filter(status='APPROVED').count(),
        'total_rejected': MentorReactivationRequest.objects.filter(status='REJECTED').count(),
    }
    
    return render(request, 'accounts/review_mentor_reactivation_requests.html', context)

@user_passes_test(lambda u: u.is_staff)
@require_POST
def approve_mentor_reactivation(request, request_id):
    """
    Approve mentor reactivation request and reactivate mentor.
    """
    try:
        reactivation_request = get_object_or_404(MentorReactivationRequest, id=request_id)
        
        # Check if already reviewed
        if reactivation_request.status != 'PENDING':
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': f'This request has already been {reactivation_request.status.lower()}.'
                }, status=400)
            messages.error(request, f'This request has already been {reactivation_request.status.lower()}.')
            return redirect('accounts:review_mentor_reactivation_requests')
        
        mentor = reactivation_request.mentor
        
        # Check if mentor is already active
        if mentor.is_active:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'This mentor is already active.'
                }, status=400)
            messages.error(request, 'This mentor is already active.')
            return redirect('accounts:review_mentor_reactivation_requests')
        
        admin_notes = request.POST.get('admin_notes', '').strip()
        
        # Store old values for audit log
        old_values = {
            'is_active': mentor.is_active,
            'accepting_mentees': mentor.accepting_mentees,
            'availability_status': mentor.availability_status,
        }
        
        # Reactivate mentor
        with transaction.atomic():
            mentor.is_active = True
            mentor.accepting_mentees = True
            mentor.availability_status = 'AVAILABLE'
            # Keep removal fields for history
            mentor.save()
            
            # Update reactivation request
            reactivation_request.status = 'APPROVED'
            reactivation_request.reviewed_at = timezone.now()
            reactivation_request.reviewed_by = request.user
            reactivation_request.admin_notes = admin_notes
            reactivation_request.save()
            
            # Create audit log for mentor reactivation
            content_type = ContentType.objects.get_for_model(Mentor)
            
            # Get request info
            ip_address = None
            user_agent = None
            request_path = None
            if hasattr(request, 'META'):
                ip_address = request.META.get('REMOTE_ADDR')
                user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
                request_path = request.path[:500]
            
            # Create audit log
            audit_log = AuditLog.objects.create(
                content_type=content_type,
                object_id=mentor.id,
                action='UPDATE',
                model_name='mentor',
                app_label='accounts',
                user=request.user,
                username=request.user.username,
                old_values=old_values,
                new_values={
                    'is_active': True,
                    'accepting_mentees': True,
                    'availability_status': 'AVAILABLE',
                },
                changed_fields=['is_active', 'accepting_mentees', 'availability_status'],
                ip_address=ip_address,
                user_agent=user_agent,
                request_path=request_path,
                message=f"Mentor reactivated: {mentor.user.get_full_name()} - Approved reactivation request",
                timestamp=timezone.now(),
            )
            
            # Create audit log for reactivation request approval
            reactivation_content_type = ContentType.objects.get_for_model(MentorReactivationRequest)
            
            reactivation_audit_log = AuditLog.objects.create(
                content_type=reactivation_content_type,
                object_id=reactivation_request.id,
                action='UPDATE',
                model_name='mentor_reactivation_request',
                app_label='accounts',
                user=request.user,
                username=request.user.username,
                old_values={'status': 'PENDING'},
                new_values={
                    'status': 'APPROVED',
                    'reviewed_at': str(reactivation_request.reviewed_at),
                    'reviewed_by': request.user.username,
                    'admin_notes': admin_notes[:200] if admin_notes else None,
                },
                changed_fields=['status', 'reviewed_at', 'reviewed_by', 'admin_notes'],
                ip_address=ip_address,
                user_agent=user_agent,
                request_path=request_path,
                message=f"Mentor reactivation request approved: {mentor.user.get_full_name()}",
                timestamp=timezone.now(),
            )
            
            # Log to Python logger
            logger.info(
                f"Mentor reactivation approved: Request ID={reactivation_request.id}, Mentor ID={mentor.id}, "
                f"Approved by={request.user.username}",
                extra={
                    'reactivation_request_id': reactivation_request.id,
                    'mentor_id': mentor.id,
                    'user_id': mentor.user.id,
                    'approved_by': request.user.id,
                    'approved_by_username': request.user.username,
                    'action': 'approve_mentor_reactivation',
                    'audit_log_id': audit_log.id,
                    'reactivation_audit_log_id': reactivation_audit_log.id,
                }
            )
            
            # Create notification for the mentor
            notification_message = 'Your mentorship reactivation request has been approved. Your mentorship status is now active and you can accept mentees again.'
            if admin_notes:
                notification_message += f'\n\nAdmin Notes: {admin_notes[:500]}'
            
            Notification.create_notification(
                recipient=mentor.user,
                notification_type='mentorship_reactivation_approved',
                title='Your Mentorship Reactivation Request Has Been Approved',
                message=notification_message,
                sender=request.user,
                content_object=reactivation_request,
                action_url=reverse('mentorship:mentor_dashboard')
            )
        
        success_message = f'Mentor "{mentor.user.get_full_name()}" has been successfully reactivated.'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': success_message
            })
        
        messages.success(request, success_message)
        return redirect('accounts:review_mentor_reactivation_requests')
        
    except Exception as e:
        logger.error(
            f"Error approving mentor reactivation: {str(e)}",
            extra={
                'request_id': request_id,
                'approved_by': request.user.id if request.user.is_authenticated else None,
                'error_type': type(e).__name__
            },
            exc_info=True
        )
        
        error_message = f'An error occurred while approving the reactivation: {str(e)}'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': error_message
            }, status=500)
        
        messages.error(request, error_message)
        return redirect('accounts:review_mentor_reactivation_requests')

@user_passes_test(lambda u: u.is_staff)
@require_POST
def reject_mentor_reactivation(request, request_id):
    """
    Reject mentor reactivation request.
    """
    try:
        reactivation_request = get_object_or_404(MentorReactivationRequest, id=request_id)
        
        # Check if already reviewed
        if reactivation_request.status != 'PENDING':
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': f'This request has already been {reactivation_request.status.lower()}.'
                }, status=400)
            messages.error(request, f'This request has already been {reactivation_request.status.lower()}.')
            return redirect('accounts:review_mentor_reactivation_requests')
        
        admin_notes = request.POST.get('admin_notes', '').strip()
        
        if not admin_notes:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Admin notes are required when rejecting a request.'
                }, status=400)
            messages.error(request, 'Admin notes are required when rejecting a request.')
            return redirect('accounts:review_mentor_reactivation_requests')
        
        mentor = reactivation_request.mentor
        
        # Update reactivation request
        with transaction.atomic():
            reactivation_request.status = 'REJECTED'
            reactivation_request.reviewed_at = timezone.now()
            reactivation_request.reviewed_by = request.user
            reactivation_request.admin_notes = admin_notes
            reactivation_request.save()
            
            # Create audit log for reactivation request rejection
            content_type = ContentType.objects.get_for_model(MentorReactivationRequest)
            
            # Get request info
            ip_address = None
            user_agent = None
            request_path = None
            if hasattr(request, 'META'):
                ip_address = request.META.get('REMOTE_ADDR')
                user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
                request_path = request.path[:500]
            
            # Create audit log
            audit_log = AuditLog.objects.create(
                content_type=content_type,
                object_id=reactivation_request.id,
                action='UPDATE',
                model_name='mentor_reactivation_request',
                app_label='accounts',
                user=request.user,
                username=request.user.username,
                old_values={'status': 'PENDING'},
                new_values={
                    'status': 'REJECTED',
                    'reviewed_at': str(reactivation_request.reviewed_at),
                    'reviewed_by': request.user.username,
                    'admin_notes': admin_notes[:200],
                },
                changed_fields=['status', 'reviewed_at', 'reviewed_by', 'admin_notes'],
                ip_address=ip_address,
                user_agent=user_agent,
                request_path=request_path,
                message=f"Mentor reactivation request rejected: {mentor.user.get_full_name()} - Reason: {admin_notes[:200]}",
                timestamp=timezone.now(),
            )
            
            # Log to Python logger
            logger.info(
                f"Mentor reactivation rejected: Request ID={reactivation_request.id}, Mentor ID={mentor.id}, "
                f"Rejected by={request.user.username}, Reason={admin_notes[:200]}",
                extra={
                    'reactivation_request_id': reactivation_request.id,
                    'mentor_id': mentor.id,
                    'user_id': mentor.user.id,
                    'rejected_by': request.user.id,
                    'rejected_by_username': request.user.username,
                    'rejection_reason': admin_notes[:200],
                    'action': 'reject_mentor_reactivation',
                    'audit_log_id': audit_log.id,
                }
            )
            
            # Create notification for the mentor
            notification_message = 'Your mentorship reactivation request has been rejected. Your mentorship status remains inactive.'
            if admin_notes:
                notification_message += f'\n\nReason: {admin_notes[:500]}'
            
            Notification.create_notification(
                recipient=mentor.user,
                notification_type='mentorship_reactivation_rejected',
                title='Your Mentorship Reactivation Request Has Been Rejected',
                message=notification_message,
                sender=request.user,
                content_object=reactivation_request,
                action_url=reverse('mentorship:mentor_dashboard')
            )
        
        success_message = f'Reactivation request for "{mentor.user.get_full_name()}" has been rejected.'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': success_message
            })
        
        messages.success(request, success_message)
        return redirect('accounts:review_mentor_reactivation_requests')
        
    except Exception as e:
        logger.error(
            f"Error rejecting mentor reactivation: {str(e)}",
            extra={
                'request_id': request_id,
                'rejected_by': request.user.id if request.user.is_authenticated else None,
                'error_type': type(e).__name__
            },
            exc_info=True
        )
        
        error_message = f'An error occurred while rejecting the reactivation: {str(e)}'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': error_message
            }, status=500)
        
        messages.error(request, error_message)
        return redirect('accounts:review_mentor_reactivation_requests')

@user_passes_test(lambda u: u.is_staff)
@require_POST
def reactivate_mentor_direct(request, mentor_id):
    """
    Admin direct reactivation of mentor (bypass request process).
    """
    try:
        mentor = get_object_or_404(Mentor, id=mentor_id)
        
        # Check if mentor is already active
        if mentor.is_active:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'This mentor is already active.'
                }, status=400)
            messages.error(request, 'This mentor is already active.')
            return redirect('accounts:admin_mentor_list')
        
        # Store old values for audit log
        old_values = {
            'is_active': mentor.is_active,
            'accepting_mentees': mentor.accepting_mentees,
            'availability_status': mentor.availability_status,
        }
        
        # Reactivate mentor
        with transaction.atomic():
            mentor.is_active = True
            mentor.accepting_mentees = True
            mentor.availability_status = 'AVAILABLE'
            # Keep removal fields for history
            mentor.save()
            
            # Create audit log
            content_type = ContentType.objects.get_for_model(Mentor)
            
            # Get request info
            ip_address = None
            user_agent = None
            request_path = None
            if hasattr(request, 'META'):
                ip_address = request.META.get('REMOTE_ADDR')
                user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
                request_path = request.path[:500]
            
            # Create audit log
            audit_log = AuditLog.objects.create(
                content_type=content_type,
                object_id=mentor.id,
                action='UPDATE',
                model_name='mentor',
                app_label='accounts',
                user=request.user,
                username=request.user.username,
                old_values=old_values,
                new_values={
                    'is_active': True,
                    'accepting_mentees': True,
                    'availability_status': 'AVAILABLE',
                },
                changed_fields=['is_active', 'accepting_mentees', 'availability_status'],
                ip_address=ip_address,
                user_agent=user_agent,
                request_path=request_path,
                message=f"Mentor reactivated directly by admin: {mentor.user.get_full_name()}",
                timestamp=timezone.now(),
            )
            
            # Log to Python logger
            logger.info(
                f"Mentor reactivated directly: Mentor ID={mentor.id}, User ID={mentor.user.id}, "
                f"Reactivated by={request.user.username}",
                extra={
                    'mentor_id': mentor.id,
                    'user_id': mentor.user.id,
                    'reactivated_by': request.user.id,
                    'reactivated_by_username': request.user.username,
                    'action': 'direct_mentor_reactivation',
                    'audit_log_id': audit_log.id,
                }
            )
        
        success_message = f'Mentor "{mentor.user.get_full_name()}" has been successfully reactivated.'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': success_message
            })
        
        messages.success(request, success_message)
        return redirect('accounts:admin_mentor_list')
        
    except Exception as e:
        logger.error(
            f"Error reactivating mentor directly: {str(e)}",
            extra={
                'mentor_id': mentor_id,
                'reactivated_by': request.user.id if request.user.is_authenticated else None,
                'error_type': type(e).__name__
            },
            exc_info=True
        )
        
        error_message = f'An error occurred while reactivating the mentor: {str(e)}'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': error_message
            }, status=500)
        
        messages.error(request, error_message)
        return redirect('accounts:admin_mentor_list')

@login_required
@require_POST
def delete_experience(request, pk):
    try:
        experience = get_object_or_404(Experience, pk=pk, profile=request.user.profile)
        experience_company = experience.company
        experience.delete()
        messages.success(request, f'🗑️ Work experience at "{experience_company}" has been deleted successfully!')
        return redirect('accounts:profile_detail')
    except Exception as e:
        messages.error(request, f'❌ Failed to delete work experience: {str(e)}')
        return redirect('accounts:profile_detail')

@login_required
def edit_experience(request, pk):
    experience = get_object_or_404(Experience, pk=pk, profile=request.user.profile)
    
    if request.method == 'POST':
        form = ExperienceForm(request.POST, instance=experience)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f'💼 Work experience at "{experience.company}" has been updated successfully!')
                return redirect('accounts:profile_detail')
            except Exception as e:
                messages.error(request, f'❌ Failed to update work experience: {str(e)}')
                return redirect('accounts:profile_detail')
        else:
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")
            messages.error(request, f'❌ Please correct the following errors: {", ".join(error_messages)}')
            return redirect('accounts:profile_detail')
    
    if request.GET.get('form_only'):
        form = ExperienceForm(instance=experience)
        return render(request, 'accounts/forms/experience_form.html', {'form': form})
    
    return redirect('accounts:profile_detail')
