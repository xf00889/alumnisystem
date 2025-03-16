from django.contrib import admin
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
        ('External Source Information', {
            'fields': ('source', 'external_id', 'last_scraped'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.posted_by = request.user
        super().save_model(request, obj, form, change)

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
