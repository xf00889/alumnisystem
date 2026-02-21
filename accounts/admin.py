from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import gettext_lazy as _
from django.contrib.admin.sites import NotRegistered
from django.forms import ModelForm
from .models import Profile, Education, Experience, Skill, Document, SkillMatch, MentorApplication, Mentor, MentorshipRequest, MentorReactivationRequest
from django.utils import timezone
from django.urls import path, reverse
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from log_viewer.models import AuditLog
import logging

logger = logging.getLogger(__name__)

User = get_user_model()

# Safely unregister the default User admin
try:
    admin.site.unregister(User)
except NotRegistered:
    pass

class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = '__all__'

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'username') if hasattr(User, 'username') else ('email',)

class ProfileAdminForm(ModelForm):
    class Meta:
        model = Profile
        fields = '__all__'

class ProfileInline(admin.StackedInline):
    model = Profile
    form = ProfileAdminForm
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

class EducationInline(admin.StackedInline):
    model = Education
    extra = 1

class ExperienceInline(admin.StackedInline):
    model = Experience
    extra = 1

class SkillInline(admin.TabularInline):
    model = Skill
    extra = 3

class DocumentInline(admin.TabularInline):
    model = Document
    extra = 1

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active') if hasattr(User, 'username') else ('email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name') if hasattr(User, 'username') else ('email', 'first_name', 'last_name')
    ordering = ('username',) if hasattr(User, 'username') else ('email',)
    inlines = (ProfileInline,)
    
    fieldsets = (
        (None, {'fields': ('username', 'password') if hasattr(User, 'username') else ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email') if hasattr(User, 'username') else ('first_name', 'last_name')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (('username', 'email') if hasattr(User, 'username') else ('email',)) + 
                     ('password1', 'password2', 'is_staff', 'is_active')}
        ),
    )

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    form = ProfileAdminForm
    list_display = ('user', 'phone_number', 'birth_date', 'country', 'is_hr', 'is_alumni_coordinator')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'phone_number')
    list_filter = ('is_hr', 'is_alumni_coordinator', 'is_public', 'created_at')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Personal Information', {
            'fields': ('avatar', 'bio', 'birth_date', 'gender')
        }),
        ('Professional Information', {
            'fields': ('current_position', 'current_employer', 'industry', 'employment_status', 'salary_range')
        }),
        ('Contact Information (Legacy)', {
            'fields': ('phone_number', 'address', 'city', 'state', 'country', 'postal_code'),
            'classes': ('collapse',)
        }),
        ('Social Media (Legacy)', {
            'fields': ('linkedin_profile', 'facebook_profile', 'twitter_profile'),
            'classes': ('collapse',)
        }),
        ('Permissions & Roles', {
            'fields': ('is_hr', 'is_alumni_coordinator', 'is_public'),
            'description': 'is_alumni_coordinator: Grants admin access but blocks system configuration'
        }),
        ('Metadata', {
            'fields': ('has_completed_registration', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    actions = ['make_alumni_coordinator', 'remove_alumni_coordinator']
    
    def make_alumni_coordinator(self, request, queryset):
        """Bulk action to assign Alumni Coordinator role"""
        updated = queryset.update(is_alumni_coordinator=True)
        self.message_user(
            request,
            f'{updated} user(s) successfully assigned as Alumni Coordinator(s).'
        )
    make_alumni_coordinator.short_description = "Assign Alumni Coordinator role"
    
    def remove_alumni_coordinator(self, request, queryset):
        """Bulk action to remove Alumni Coordinator role"""
        updated = queryset.update(is_alumni_coordinator=False)
        self.message_user(
            request,
            f'{updated} user(s) successfully removed from Alumni Coordinator role.'
        )
    remove_alumni_coordinator.short_description = "Remove Alumni Coordinator role"
    inlines = [EducationInline, ExperienceInline, SkillInline, DocumentInline]
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'avatar', 'bio')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'country', 'city', 'address')
        }),
        ('Personal Information', {
            'fields': ('birth_date', 'gender')
        }),
        ('Professional Information', {
            'fields': (
                'current_position',
                'current_employer',
                'industry',
                'employment_status',
                'salary_range'
            )
        }),
        ('Permissions', {
            'fields': ('is_hr',),
            'description': 'HR users can post jobs and manage job applications.'
        }),
        ('Settings', {
            'fields': ('is_public', 'has_completed_registration')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ('profile', 'program', 'school', 'graduation_year')
    search_fields = ('profile__user__email', 'major', 'school')
    list_filter = ('program', 'school', 'graduation_year')

@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('profile', 'company', 'position', 'is_current')
    search_fields = ('profile__user__email', 'company', 'position')
    list_filter = ('is_current',)

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'profile', 'skill_type', 'proficiency_level', 'years_of_experience', 'is_primary')
    list_filter = ('skill_type', 'proficiency_level', 'is_primary')
    search_fields = ('name', 'profile__user__username', 'profile__user__email')
    ordering = ('name',)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('profile', 'profile__user')

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('profile', 'title', 'document_type', 'uploaded_at')
    search_fields = ('profile__user__email', 'title')
    list_filter = ('document_type', 'uploaded_at')

@admin.register(SkillMatch)
class SkillMatchAdmin(admin.ModelAdmin):
    list_display = ('profile', 'job', 'match_score', 'is_applied', 'created_at')
    list_filter = ('is_applied', 'created_at')
    search_fields = ('profile__user__username', 'job__job_title', 'job__company_name')
    ordering = ('-match_score',)
    readonly_fields = ('match_score', 'matched_skills', 'missing_skills')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('profile', 'profile__user', 'job')

@admin.register(MentorApplication)
class MentorApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'years_of_experience', 'status', 'application_date', 'review_date')
    list_filter = ('status', 'application_date', 'review_date')
    search_fields = ('user__username', 'user__email', 'expertise_areas', 'competency_summary')
    readonly_fields = ('application_date',)
    fieldsets = (
        ('Applicant Information', {
            'fields': ('user', 'years_of_experience', 'expertise_areas')
        }),
        ('Documents', {
            'fields': ('certifications', 'training_documents')
        }),
        ('Application Details', {
            'fields': ('competency_summary', 'status', 'review_notes', 'reviewed_by', 'review_date')
        }),
    )

    def save_model(self, request, obj, form, change):
        if 'status' in form.changed_data:
            obj.review_date = timezone.now()
            obj.reviewed_by = request.user
            
            # If approved, create or update Mentor profile
            if obj.status == 'APPROVED':
                mentor, created = Mentor.objects.get_or_create(user=obj.user)
                mentor.expertise_areas = obj.expertise_areas
                mentor.is_verified = True
                mentor.verification_date = timezone.now()
                mentor.verified_by = request.user
                mentor.save()
        
        super().save_model(request, obj, form, change)

@admin.register(Mentor)
class MentorAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_email', 'is_verified', 'availability_status', 'current_mentees', 'max_mentees', 'accepting_mentees', 'created_at')
    list_filter = ('is_verified', 'availability_status', 'is_active', 'accepting_mentees', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'expertise_areas')
    readonly_fields = ('current_mentees', 'verification_date', 'verified_by', 'created_at', 'updated_at')
    actions = ['verify_mentors', 'make_available', 'make_unavailable', 'remove_mentors']
    list_per_page = 20
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'expertise_areas', 'mentoring_experience')
        }),
        ('Verification', {
            'fields': ('is_verified', 'verification_date', 'verified_by')
        }),
        ('Availability', {
            'fields': ('availability_status', 'max_mentees', 'current_mentees', 'accepting_mentees', 'is_active')
        }),
        ('Preferences', {
            'fields': ('expectations', 'preferred_contact_method')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'
    
    def verify_mentors(self, request, queryset):
        updated = queryset.update(
            is_verified=True,
            verification_date=timezone.now(),
            verified_by=request.user
        )
        self.message_user(request, f'{updated} mentors were successfully verified.')
    verify_mentors.short_description = 'Verify selected mentors'
    
    def make_available(self, request, queryset):
        updated = queryset.update(
            availability_status='AVAILABLE',
            accepting_mentees=True
        )
        self.message_user(request, f'{updated} mentors were marked as available.')
    make_available.short_description = 'Mark selected mentors as available'
    
    def make_unavailable(self, request, queryset):
        updated = queryset.update(
            availability_status='UNAVAILABLE',
            accepting_mentees=False
        )
        self.message_user(request, f'{updated} mentors were marked as unavailable.')
    make_unavailable.short_description = 'Mark selected mentors as unavailable'
    
    def remove_mentors(self, request, queryset):
        """
        Remove selected mentors (soft delete) with validation and audit logging.
        Redirects to intermediate form if reason not provided.
        """
        # Filter out already removed mentors
        active_mentors = queryset.filter(is_active=True)
        
        if not active_mentors.exists():
            self.message_user(request, 'No active mentors selected to disable.', messages.WARNING)
            return
        
        # Check for mentors with active mentorships
        mentors_with_active_mentorships = []
        for mentor in active_mentors:
            active_count = mentor.get_active_mentorships_count()
            if active_count > 0:
                mentors_with_active_mentorships.append({
                    'mentor': mentor,
                    'count': active_count
                })
        
        if mentors_with_active_mentorships:
            error_msg = 'Cannot disable the following mentors due to active mentorships:\n'
            for item in mentors_with_active_mentorships:
                error_msg += f"- {item['mentor'].user.get_full_name()}: {item['count']} active mentorship(s)\n"
            error_msg += '\nPlease complete or cancel all active mentorships before disabling these mentors.'
            self.message_user(request, error_msg, messages.ERROR)
            return
        
        # Store selected mentor IDs in session and redirect to form
        selected_ids = list(active_mentors.values_list('id', flat=True))
        request.session['remove_mentor_ids'] = selected_ids
        return HttpResponseRedirect(reverse('admin:accounts_mentor_remove_form'))
    remove_mentors.short_description = 'Disable selected mentors (requires reason)'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('remove-mentors-form/', self.admin_site.admin_view(self.remove_mentors_form_view), name='accounts_mentor_remove_form'),
        ]
        return custom_urls + urls
    
    @staff_member_required
    def remove_mentors_form_view(self, request):
        """
        Intermediate form view for removing mentors with reason.
        """
        mentor_ids = request.session.get('remove_mentor_ids', [])
        if not mentor_ids:
            messages.error(request, 'No mentors selected for removal.')
            return HttpResponseRedirect(reverse('admin:accounts_mentor_changelist'))
        
        mentors = Mentor.objects.filter(id__in=mentor_ids, is_active=True)
        
        if request.method == 'POST':
            removal_reason = request.POST.get('removal_reason', '').strip()
            if not removal_reason:
                messages.error(request, 'Removal reason is required.')
            else:
                # Process removal
                removed_count = 0
                for mentor in mentors:
                    try:
                        with transaction.atomic():
                            # Store old values for audit log
                            old_values = {
                                'is_active': mentor.is_active,
                                'accepting_mentees': mentor.accepting_mentees,
                                'availability_status': mentor.availability_status,
                            }
                            
                            # Soft delete
                            mentor.is_active = False
                            mentor.accepting_mentees = False
                            mentor.availability_status = 'UNAVAILABLE'
                            mentor.removal_reason = removal_reason
                            mentor.removed_at = timezone.now()
                            mentor.removed_by = request.user
                            mentor.save()
                            
                            # Create audit log entry
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
                                f"Mentor removed via admin: Mentor ID={mentor.id}, User ID={mentor.user.id}, "
                                f"Removed by={request.user.username}, Reason={removal_reason[:200]}",
                                extra={
                                    'mentor_id': mentor.id,
                                    'user_id': mentor.user.id,
                                    'removed_by': request.user.id,
                                    'removed_by_username': request.user.username,
                                    'removal_reason': removal_reason[:200],
                                    'action': 'mentor_removal_admin',
                                    'audit_log_id': audit_log.id,
                                }
                            )
                            
                            removed_count += 1
                    except Exception as e:
                        logger.error(
                            f"Error removing mentor via admin: {str(e)}",
                            extra={
                                'mentor_id': mentor.id,
                                'removed_by': request.user.id,
                                'error_type': type(e).__name__
                            },
                            exc_info=True
                        )
                        messages.error(request, f'Error disabling mentor {mentor.user.get_full_name()}: {str(e)}')
                
                if removed_count > 0:
                    messages.success(request, f'{removed_count} mentor(s) were successfully disabled.')
                    # Clear session
                    if 'remove_mentor_ids' in request.session:
                        del request.session['remove_mentor_ids']
                    return HttpResponseRedirect(reverse('admin:accounts_mentor_changelist'))
        
        context = {
            'title': 'Disable Mentors',
            'mentors': mentors,
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request, None),
        }
        return render(request, 'admin/accounts/mentor/remove_mentors_form.html', context)

    def save_model(self, request, obj, form, change):
        if 'is_verified' in form.changed_data and obj.is_verified:
            obj.verification_date = timezone.now()
            obj.verified_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(MentorshipRequest)
class MentorshipRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'mentor_name', 'mentee_name', 'status', 'progress_percentage', 'start_date', 'end_date', 'created_at')
    list_filter = ('status', 'start_date', 'end_date', 'created_at')
    search_fields = ('mentor__user__username', 'mentor__user__email', 'mentee__username', 'mentee__email', 'skills_seeking', 'goals')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_requests', 'mark_as_completed', 'mark_as_cancelled', 'mark_as_paused']
    list_per_page = 20
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Participants', {
            'fields': ('mentor', 'mentee')
        }),
        ('Request Details', {
            'fields': ('skills_seeking', 'goals', 'message')
        }),
        ('Status', {
            'fields': ('status', 'progress_percentage')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date', 'expected_end_date', 'timeline_milestones')
        }),
        ('Feedback', {
            'fields': ('feedback', 'rating')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def mentor_name(self, obj):
        return obj.mentor.user.get_full_name() or obj.mentor.user.username
    mentor_name.short_description = 'Mentor'
    mentor_name.admin_order_field = 'mentor__user__first_name'
    
    def mentee_name(self, obj):
        return obj.mentee.get_full_name() or obj.mentee.username
    mentee_name.short_description = 'Mentee'
    mentee_name.admin_order_field = 'mentee__first_name'
    
    def approve_requests(self, request, queryset):
        updated = queryset.filter(status='PENDING').update(
            status='APPROVED',
            start_date=timezone.now().date()
        )
        
        # Update mentor's current_mentees count for each approved request
        for mentorship in queryset.filter(status='APPROVED'):
            mentor = mentorship.mentor
            mentor.current_mentees += 1
            mentor.save()
            
        self.message_user(request, f'{updated} mentorship requests were approved.')
    approve_requests.short_description = 'Approve selected mentorship requests'
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.filter(status__in=['APPROVED', 'PAUSED']).update(
            status='COMPLETED',
            end_date=timezone.now().date()
        )
        
        # Update mentor's current_mentees count for each completed request
        for mentorship in queryset.filter(status='COMPLETED'):
            mentor = mentorship.mentor
            if mentor.current_mentees > 0:
                mentor.current_mentees -= 1
                mentor.save()
                
        self.message_user(request, f'{updated} mentorship requests were marked as completed.')
    mark_as_completed.short_description = 'Mark selected mentorships as completed'
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.filter(status__in=['APPROVED', 'PAUSED']).update(
            status='CANCELLED',
            end_date=timezone.now().date()
        )
        
        # Update mentor's current_mentees count for each cancelled request
        for mentorship in queryset.filter(status='CANCELLED'):
            mentor = mentorship.mentor
            if mentor.current_mentees > 0:
                mentor.current_mentees -= 1
                mentor.save()
                
        self.message_user(request, f'{updated} mentorship requests were marked as cancelled.')
    mark_as_cancelled.short_description = 'Mark selected mentorships as cancelled'
    
    def mark_as_paused(self, request, queryset):
        updated = queryset.filter(status='APPROVED').update(
            status='PAUSED'
        )
        self.message_user(request, f'{updated} mentorship requests were paused.')
    mark_as_paused.short_description = 'Pause selected mentorships'

# Custom admin view for mentor list
@staff_member_required
def admin_mentor_list(request):
    """
    Custom admin view to display a list of mentors with enhanced UI
    """
    # Check if the user is a staff member
    if not request.user.is_staff:
        raise PermissionDenied
        
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
    
    context = {
        'mentors': mentors,
        'title': 'Mentor List',
        'sort_by': sort_by,
        'has_add_permission': request.user.has_perm('accounts.add_mentor'),
        'has_change_permission': request.user.has_perm('accounts.change_mentor'),
    }
    return render(request, 'admin/mentor_list.html', context)

@admin.register(MentorReactivationRequest)
class MentorReactivationRequestAdmin(admin.ModelAdmin):
    list_display = ('mentor', 'requested_by', 'email', 'is_verified', 'status', 'requested_at', 'reviewed_at', 'reviewed_by')
    list_filter = ('status', 'is_verified', 'requested_at', 'reviewed_at')
    search_fields = ('mentor__user__email', 'mentor__user__first_name', 'mentor__user__last_name', 'email', 'requested_by__email')
    readonly_fields = ('requested_at', 'reviewed_at', 'verification_code_expires_at')
    date_hierarchy = 'requested_at'
    
    fieldsets = (
        ('Request Information', {
            'fields': ('mentor', 'requested_by', 'email', 'request_reason', 'requested_at')
        }),
        ('Verification', {
            'fields': ('verification_code', 'is_verified', 'verification_code_expires_at')
        }),
        ('Review', {
            'fields': ('status', 'admin_notes', 'reviewed_at', 'reviewed_by')
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status != 'PENDING':
            return self.readonly_fields + ('status', 'mentor', 'requested_by', 'email')
        return self.readonly_fields
