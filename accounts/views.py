from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, UpdateView
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponseForbidden
from django.core.exceptions import ValidationError
from .models import Profile, Education, Experience, Skill, Document
from alumni_groups.models import AlumniGroup, GroupMembership
from alumni_directory.models import Alumni
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
    DocumentUploadForm
)
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.db import transaction
from django.contrib import messages
from django.views.decorators.http import require_POST

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
                
                # Create or update Alumni record
                Alumni.objects.update_or_create(
                    user=request.user,  # This is our lookup field
                    defaults={
                        'graduation_year': form.cleaned_data.get('graduation_year'),
                        'course': form.cleaned_data.get('program'),
                        'gender': form.cleaned_data.get('gender', 'O'),  # Default to 'Other' if not provided
                        'date_of_birth': form.cleaned_data.get('date_of_birth'),
                        'province': form.cleaned_data.get('province', ''),
                        'city': form.cleaned_data.get('city', ''),
                        'address': form.cleaned_data.get('address', ''),
                        'employment_status': 'UNEMPLOYED'  # Default status
                    }
                )
                
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
                'program': education.program,
                'school': education.school,
                'graduation_year': education.graduation_year,
            })
        except Education.DoesNotExist:
            pass

        form = PostRegistrationForm(initial=initial_data)

    return render(request, 'accounts/post_registration.html', {
        'form': form,
        'title': 'Complete Registration',
    })

class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = 'accounts/profile_detail.html'
    context_object_name = 'profile'

    def get_object(self, queryset=None):
        return self.request.user.profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['education_list'] = self.object.education.all().order_by('-graduation_year')
        context['experience_list'] = self.object.experience.all().order_by('-start_date')
        context['skill_list'] = self.object.skills.all().order_by('-proficiency_level')
        return context

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

                        # Handle document uploads
                        for form in [transcript_form, certificate_form, diploma_form, resume_form]:
                            if form.is_valid() and form.has_changed():
                                if form.cleaned_data.get('file'):
                                    doc = form.save(commit=False)
                                    doc.profile = request.user.profile
                                    doc.save()

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
            
            return redirect('accounts:profile_detail')
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
