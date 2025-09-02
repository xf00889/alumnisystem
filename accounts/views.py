from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, UpdateView
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponseForbidden
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST
from .models import (
    Profile, Education, Experience, Skill, Document, SkillMatch,
    MentorApplication, Mentor
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

@login_required
def post_registration(request):
    # First, ensure the user has a profile
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)

    # Redirect if already completed registration
    if profile.has_completed_registration:
        return redirect('core:home')

    if request.method == 'POST':
        form = PostRegistrationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Save the form data
                form.save(request.user)
                
                messages.success(request, 'Registration completed successfully!')
            return redirect('core:home')
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
                                    # Save to Profile Document
                                    doc = form.save(commit=False)
                                    doc.profile = request.user.profile
                                    doc.save()

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
                                            description=doc.description,
                                            is_verified=False
                                        )
                                    except Alumni.DoesNotExist:
                                        pass

                    return JsonResponse({'status': 'success'})

                except Exception as e:
                    return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
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
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

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
    document = get_object_or_404(Document, pk=pk, profile=request.user.profile)
    document.delete()
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
            skill = form.save(commit=False)
            skill.profile = request.user.profile
            skill.save()
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'errors': form.errors})
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
            education = form.save(commit=False)
            education.profile = request.user.profile
            education.save()
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'errors': form.errors})
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
            experience = form.save(commit=False)
            experience.profile = request.user.profile
            experience.save()
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'errors': form.errors})
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
            document = form.save(commit=False)
            document.profile = request.user.profile
            document.save()
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'errors': form.errors})
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
            form.save()
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    
    if request.GET.get('form_only'):
        form = EducationForm(instance=education)
        return render(request, 'accounts/forms/education_form.html', {'form': form})
    
    return redirect('accounts:profile_detail')

@login_required
def delete_education(request, pk):
    if request.method == 'POST':
        education = get_object_or_404(Education, pk=pk, profile=request.user.profile)
        education.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})

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
        
        return JsonResponse({
            'status': 'success',
            'message': 'Career path added successfully',
            'id': experience.id
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

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
        
        return JsonResponse({
            'status': 'success',
            'message': 'Achievement added successfully',
            'id': achievement.id
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

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
            application = form.save(commit=False)
            application.user = request.user
            application.save()
            
            messages.success(request, 'Your mentor application has been submitted successfully. We will review it shortly.')
            return redirect('accounts:mentor_application_status')
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
@paginate(items_per_page=10)
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
        
        if action == 'approve':
            application.status = 'APPROVED'
            # Create or update Mentor profile
            mentor, created = Mentor.objects.get_or_create(user=application.user)
            mentor.expertise_areas = application.expertise_areas
            mentor.is_verified = True
            mentor.verification_date = timezone.now()
            mentor.verified_by = request.user
            mentor.save()
            
            messages.success(request, f'Mentor application for {application.user.get_full_name()} has been approved.')
        elif action == 'reject':
            application.status = 'REJECTED'
            messages.success(request, f'Mentor application for {application.user.get_full_name()} has been rejected.')
        
        application.save()
        
        # Send notification to user
        # TODO: Implement notification system
        
        return redirect('accounts:review_mentor_applications')
    
    # Handle GET request
    return render(request, 'accounts/review_mentor_applications.html', {
        'applications': [application]
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
    
    context = {
        'mentors': mentors,
        'total_mentors': total_mentors,
        'active_mentors': active_mentors,
        'verified_mentors': verified_mentors,
        'total_mentees': total_mentees,
        'pending_applications': pending_applications,
        'sort_by': sort_by,
    }
    return render(request, 'accounts/admin_mentor_list.html', context)

@login_required
@require_POST
def delete_experience(request, pk):
    try:
        experience = get_object_or_404(Experience, pk=pk, profile=request.user.profile)
        experience.delete()
        messages.success(request, "Work experience deleted successfully.")
        return JsonResponse({'status': 'success'})
    except Exception as e:
        messages.error(request, f"Error deleting experience: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
def edit_experience(request, pk):
    experience = get_object_or_404(Experience, pk=pk, profile=request.user.profile)
    
    if request.method == 'POST':
        form = ExperienceForm(request.POST, instance=experience)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    
    if request.GET.get('form_only'):
        form = ExperienceForm(instance=experience)
        return render(request, 'accounts/forms/experience_form.html', {'form': form})
    
    return redirect('accounts:profile_detail')
