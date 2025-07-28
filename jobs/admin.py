from django.contrib import admin
from django.contrib import messages
from .models import JobPosting, JobApplication

@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ('job_title', 'company_name', 'location', 'job_type', 'source_type', 'posted_date', 'is_featured', 'is_active')
    list_filter = ('job_type', 'source_type', 'is_featured', 'is_active', 'posted_date', 'accepts_internal_applications')
    search_fields = ('job_title', 'company_name', 'location', 'job_description')
    prepopulated_fields = {'slug': ('job_title', 'company_name',)}
    date_hierarchy = 'posted_date'
    ordering = ('-posted_date',)
    list_per_page = 20
    fieldsets = (
        ('Basic Information', {
            'fields': ('job_title', 'slug', 'company_name', 'location', 'job_type', 'job_description')
        }),
        ('Application Details', {
            'fields': ('source_type', 'application_link', 'accepts_internal_applications', 'required_documents')
        }),
        ('Additional Information', {
            'fields': ('salary_range', 'is_featured', 'is_active', 'posted_by')
        }),

    )

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.posted_by = request.user
        super().save_model(request, obj, form, change)
    
    # Custom admin actions
    def make_featured(self, request, queryset):
        """Mark selected job postings as featured"""
        updated = queryset.update(is_featured=True)
        messages.success(request, f'{updated} job posting(s) marked as featured.')
    make_featured.short_description = "Mark selected jobs as featured"
    
    def remove_featured(self, request, queryset):
        """Remove featured status from selected job postings"""
        updated = queryset.update(is_featured=False)
        messages.success(request, f'{updated} job posting(s) removed from featured.')
    remove_featured.short_description = "Remove featured status from selected jobs"
    
    def activate_jobs(self, request, queryset):
        """Activate selected job postings"""
        updated = queryset.update(is_active=True)
        messages.success(request, f'{updated} job posting(s) activated.')
    activate_jobs.short_description = "Activate selected jobs"
    
    def deactivate_jobs(self, request, queryset):
        """Deactivate selected job postings"""
        updated = queryset.update(is_active=False)
        messages.success(request, f'{updated} job posting(s) deactivated.')
    deactivate_jobs.short_description = "Deactivate selected jobs"
    
    actions = ['make_featured', 'remove_featured', 'activate_jobs', 'deactivate_jobs']

@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'job', 'status', 'application_date', 'last_updated')
    list_filter = ('status', 'application_date', 'job__source_type')
    search_fields = ('applicant__username', 'applicant__email', 'job__job_title', 'notes')
    date_hierarchy = 'application_date'
    ordering = ('-application_date',)
    raw_id_fields = ('applicant', 'job')
    list_per_page = 20
    fieldsets = (
        ('Application Information', {
            'fields': ('job', 'applicant', 'status', 'cover_letter')
        }),
        ('Documents', {
            'fields': ('resume', 'additional_documents')
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return ('job', 'applicant', 'application_date')
        return ('application_date',)
    
    # Custom admin actions for job applications
    def mark_as_shortlisted(self, request, queryset):
        """Mark selected applications as shortlisted"""
        updated = queryset.update(status='SHORTLISTED')
        messages.success(request, f'{updated} application(s) marked as shortlisted.')
    mark_as_shortlisted.short_description = "Mark selected applications as shortlisted"
    
    def mark_as_interviewed(self, request, queryset):
        """Mark selected applications as interviewed"""
        updated = queryset.update(status='INTERVIEWED')
        messages.success(request, f'{updated} application(s) marked as interviewed.')
    mark_as_interviewed.short_description = "Mark selected applications as interviewed"
    
    def mark_as_accepted(self, request, queryset):
        """Mark selected applications as accepted"""
        updated = queryset.update(status='ACCEPTED')
        messages.success(request, f'{updated} application(s) marked as accepted.')
    mark_as_accepted.short_description = "Mark selected applications as accepted"
    
    def mark_as_rejected(self, request, queryset):
        """Mark selected applications as rejected"""
        updated = queryset.update(status='REJECTED')
        messages.success(request, f'{updated} application(s) marked as rejected.')
    mark_as_rejected.short_description = "Mark selected applications as rejected"
    
    actions = ['mark_as_shortlisted', 'mark_as_interviewed', 'mark_as_accepted', 'mark_as_rejected']
