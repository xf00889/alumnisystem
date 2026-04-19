from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import JobPosting, JobApplication, JobPreference, ScrapedJob, UserJobAIScore

@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ('job_title', 'company_name', 'location', 'job_type', 'source_type', 'posted_by', 'posted_date', 'is_featured', 'is_active')
    list_filter = ('job_type', 'source_type', 'is_featured', 'is_active', 'posted_by', 'posted_date', 'accepts_internal_applications')
    search_fields = ('job_title', 'company_name', 'location', 'job_description', 'posted_by__username', 'posted_by__email')
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

@admin.register(JobPreference)
class JobPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_configured', 'updated_at', 'modification_count')
    list_filter = ('is_configured', 'skill_matching_enabled', 'remote_only', 'willing_to_relocate', 'source_type')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at', 'first_configured_at', 'modification_count')
    date_hierarchy = 'updated_at'
    ordering = ('-updated_at',)
    list_per_page = 20
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Configuration Status', {
            'fields': ('is_configured', 'was_prompted')
        }),
        ('Hard Filters', {
            'fields': ('job_types', 'location_text', 'remote_only', 'willing_to_relocate', 'minimum_salary', 'source_type'),
            'description': 'Exclusionary filters that remove non-matching jobs'
        }),
        ('Soft Filters', {
            'fields': ('industries', 'experience_levels'),
            'description': 'Scoring filters that rank matching jobs'
        }),
        ('Skill Matching', {
            'fields': ('skill_matching_enabled', 'skill_match_threshold')
        }),
        ('Analytics', {
            'fields': ('created_at', 'updated_at', 'first_configured_at', 'modification_count'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return self.readonly_fields + ('user',)
        return self.readonly_fields


@admin.register(UserJobAIScore)
class UserJobAIScoreAdmin(admin.ModelAdmin):
    list_display = ('user', 'job', 'score', 'status', 'profile_version', 'computed_at', 'updated_at')
    list_filter = ('status', 'profile_version', 'computed_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'job__job_title', 'job__company_name')
    readonly_fields = (
        'user',
        'job',
        'score',
        'reason',
        'strengths_json',
        'gaps_json',
        'status',
        'error_message',
        'profile_version',
        'computed_at',
        'updated_at',
        'created_at',
    )
    ordering = ('-computed_at', '-updated_at')


# ─────────────────────────────────────────────────────────────────────────────
# ScrapedJob Admin — scrape + publish workflow
# ─────────────────────────────────────────────────────────────────────────────

class ScrapeJobsForm(admin.helpers.ActionForm):
    """Inline form shown above the ScrapedJob changelist for triggering a scrape."""
    pass


@admin.register(ScrapedJob)
class ScrapedJobAdmin(admin.ModelAdmin):
    list_display = (
        "search_keyword",
        "search_location",
        "source_display",
        "total_found",
        "scraped_by",
        "scraped_at",
        "is_active",
        "publish_button",
    )
    list_filter = ("source", "is_active", "scraped_at", "scraped_by")
    search_fields = ("search_keyword", "search_location", "scraped_by__username")
    readonly_fields = ("scraped_at", "total_found", "scraped_by", "jobs_preview")
    date_hierarchy = "scraped_at"
    ordering = ("-scraped_at",)
    list_per_page = 20

    fieldsets = (
        ("Search Parameters", {
            "fields": ("search_keyword", "search_location", "source", "is_active"),
        }),
        ("Results", {
            "fields": ("total_found", "scraped_by", "scraped_at", "jobs_preview"),
        }),
        ("Raw Data", {
            "fields": ("scraped_data",),
            "classes": ("collapse",),
        }),
    )

    # ── Custom URL for the "Scrape Now" page ─────────────────────────────────

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "scrape-now/",
                self.admin_site.admin_view(self.scrape_now_view),
                name="jobs_scrapedjob_scrape_now",
            ),
            path(
                "<int:pk>/publish/",
                self.admin_site.admin_view(self.publish_single_view),
                name="jobs_scrapedjob_publish_single",
            ),
        ]
        return custom + urls

    # ── "Scrape Now" view ─────────────────────────────────────────────────────

    def scrape_now_view(self, request):
        """
        Custom admin page with a form to trigger a multi-site scrape.
        GET  → show form
        POST → run scrapers, save ScrapedJob records, redirect to changelist
        """
        from .botasaurus_scrapers.orchestrator import SCRAPERS, scrape_all_sites
        from django import forms as django_forms

        class ScrapeForm(django_forms.Form):
            keyword = django_forms.CharField(
                max_length=100,
                label="Job keyword",
                widget=django_forms.TextInput(attrs={
                    "class": "vTextField",
                    "placeholder": "e.g. software engineer",
                    "autofocus": True,
                }),
            )
            location = django_forms.CharField(
                max_length=100,
                label="Location",
                initial="Philippines",
                widget=django_forms.TextInput(attrs={
                    "class": "vTextField",
                    "placeholder": "e.g. Manila, Cebu, Philippines",
                }),
            )
            sources = django_forms.MultipleChoiceField(
                choices=[(k, v[0]) for k, v in SCRAPERS.items()],
                initial=list(SCRAPERS.keys()),
                widget=django_forms.CheckboxSelectMultiple,
                label="Sites to scrape",
                required=True,
            )

        context = {
            **self.admin_site.each_context(request),
            "title": "Scrape Jobs from Philippine Job Sites",
            "opts": self.model._meta,
            "has_permission": True,
        }

        if request.method == "POST":
            form = ScrapeForm(request.POST)
            if form.is_valid():
                keyword = form.cleaned_data["keyword"]
                location = form.cleaned_data["location"]
                sources = form.cleaned_data["sources"]

                self.message_user(
                    request,
                    f"Scraping '{keyword}' in '{location}' from {len(sources)} site(s)… "
                    "This may take up to 60 seconds.",
                    messages.INFO,
                )

                try:
                    results = scrape_all_sites(keyword, location, sources=sources, max_workers=4)
                except Exception as exc:
                    self.message_user(request, f"Scraping failed: {exc}", messages.ERROR)
                    context["form"] = form
                    return render(request, "admin/jobs/scrapedjob/scrape_now.html", context)

                saved = 0
                total_jobs = 0
                for result in results:
                    if not result.get("jobs"):
                        continue
                    src = result.get("source", "OTHER")
                    # Deactivate previous entries for same search + source
                    ScrapedJob.objects.filter(
                        search_keyword=keyword,
                        search_location=location,
                        source=src,
                        scraped_by=request.user,
                    ).update(is_active=False)

                    ScrapedJob.objects.create(
                        search_keyword=keyword,
                        search_location=location,
                        source=src,
                        scraped_data=result,
                        total_found=result.get("total_found", 0),
                        scraped_by=request.user,
                    )
                    saved += 1
                    total_jobs += result.get("total_found", 0)

                self.message_user(
                    request,
                    f"Done! Saved {saved} scrape record(s) with {total_jobs} total job(s). "
                    "Use 'Publish to Job Board' to make them visible to users.",
                    messages.SUCCESS,
                )
                return HttpResponseRedirect(
                    reverse("admin:jobs_scrapedjob_changelist")
                )
        else:
            form = ScrapeForm()

        context["form"] = form
        return render(request, "admin/jobs/scrapedjob/scrape_now.html", context)

    # ── Publish single record view ────────────────────────────────────────────

    def publish_single_view(self, request, pk):
        """Publish a single ScrapedJob record to the job board."""
        from .admin_scraper_utils import publish_scraped_job

        scraped_job = ScrapedJob.objects.get(pk=pk)
        summary = publish_scraped_job(scraped_job, posted_by=request.user)

        self.message_user(
            request,
            f"Published {summary['published']} new job(s), "
            f"skipped {summary['skipped']} duplicate(s), "
            f"{summary['errors']} error(s).",
            messages.SUCCESS if summary["errors"] == 0 else messages.WARNING,
        )
        return HttpResponseRedirect(reverse("admin:jobs_scrapedjob_changelist"))

    # ── Admin actions ─────────────────────────────────────────────────────────

    @admin.action(description="Publish selected scraped jobs to the Job Board")
    def publish_to_job_board(self, request, queryset):
        from .admin_scraper_utils import publish_multiple_scraped_jobs

        summary = publish_multiple_scraped_jobs(queryset, posted_by=request.user)
        self.message_user(
            request,
            f"Published {summary['published']} new job(s), "
            f"skipped {summary['skipped']} duplicate(s), "
            f"{summary['errors']} error(s).",
            messages.SUCCESS if summary["errors"] == 0 else messages.WARNING,
        )

    @admin.action(description="Deactivate selected scrape records")
    def deactivate_records(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} record(s) deactivated.", messages.SUCCESS)

    actions = ["publish_to_job_board", "deactivate_records"]

    # ── Custom display columns ────────────────────────────────────────────────

    def source_display(self, obj):
        return obj.get_source_display()
    source_display.short_description = "Source"

    def publish_button(self, obj):
        url = reverse("admin:jobs_scrapedjob_publish_single", args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" style="'
            'background:#417690;color:#fff;padding:4px 10px;'
            'border-radius:4px;text-decoration:none;font-size:12px;">'
            '▶ Publish</a>',
            url,
        )
    publish_button.short_description = "Publish"
    publish_button.allow_tags = True

    def jobs_preview(self, obj):
        """Show first 5 jobs from the scraped data as a preview table."""
        jobs = obj.jobs_data[:5]
        if not jobs:
            return "No jobs in this record."
        rows = ""
        for job in jobs:
            rows += (
                f"<tr>"
                f"<td style='padding:4px 8px;border-bottom:1px solid #eee'>{job.get('title','—')}</td>"
                f"<td style='padding:4px 8px;border-bottom:1px solid #eee'>{job.get('company','—')}</td>"
                f"<td style='padding:4px 8px;border-bottom:1px solid #eee'>{job.get('location','—')}</td>"
                f"<td style='padding:4px 8px;border-bottom:1px solid #eee'>{job.get('salary','—')}</td>"
                f"</tr>"
            )
        return mark_safe(
            f"<table style='border-collapse:collapse;font-size:13px;width:100%'>"
            f"<thead><tr>"
            f"<th style='text-align:left;padding:4px 8px;background:#f8f8f8'>Title</th>"
            f"<th style='text-align:left;padding:4px 8px;background:#f8f8f8'>Company</th>"
            f"<th style='text-align:left;padding:4px 8px;background:#f8f8f8'>Location</th>"
            f"<th style='text-align:left;padding:4px 8px;background:#f8f8f8'>Salary</th>"
            f"</tr></thead><tbody>{rows}</tbody></table>"
            f"<p style='color:#666;font-size:12px'>Showing first 5 of {obj.total_found} job(s).</p>"
        )
    jobs_preview.short_description = "Jobs Preview"

    # ── Changelist page — add "Scrape Now" button ─────────────────────────────

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["scrape_now_url"] = reverse("admin:jobs_scrapedjob_scrape_now")
        return super().changelist_view(request, extra_context=extra_context)
