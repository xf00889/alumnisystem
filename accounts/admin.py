from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.translation import gettext_lazy as _
from django.contrib.admin.sites import NotRegistered
from django.forms import ModelForm
from .models import Profile, Education, Experience, Skill, Document, SkillMatch, MentorApplication, Mentor, MentorshipRequest
from django.utils import timezone
from django.urls import path
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied

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
    list_display = ('user', 'phone_number', 'birth_date', 'country')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'phone_number')
    list_filter = ('is_public', 'created_at')
    inlines = [EducationInline, ExperienceInline, SkillInline, DocumentInline]
    readonly_fields = ('created_at', 'updated_at')

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
    actions = ['verify_mentors', 'make_available', 'make_unavailable']
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
