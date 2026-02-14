from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    SiteConfig, PageSection, StaffMember, 
    TimelineItem, ContactInfo, FAQ, Feature, Testimonial,
    AboutPageConfig, AlumniStatistic, FooterLink
)


@admin.register(SiteConfig)
class SiteConfigAdmin(admin.ModelAdmin):
    """
    Admin interface for Site Configuration (Singleton)
    """
    list_display = ['site_name', 'contact_email', 'contact_phone', 'created']
    list_filter = ['created', 'modified']
    search_fields = ['site_name', 'contact_email', 'contact_phone']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('site_name', 'site_tagline', 'logo')
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'contact_phone', 'contact_address')
        }),
        ('Social Media', {
            'fields': ('facebook_url', 'twitter_url', 'linkedin_url', 'instagram_url', 'youtube_url'),
            'classes': ('collapse',)
        }),
        ('Button Texts', {
            'fields': ('signup_button_text', 'login_button_text'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Prevent adding multiple SiteConfig instances"""
        return not SiteConfig.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deleting the SiteConfig instance"""
        return False
    
    def changelist_view(self, request, extra_context=None):
        """Redirect to the single instance if it exists"""
        if SiteConfig.objects.exists():
            obj = SiteConfig.objects.first()
            return admin.ModelAdmin.change_view(
                self, request, str(obj.pk), extra_context
            )
        return super().changelist_view(request, extra_context)


@admin.register(PageSection)
class PageSectionAdmin(admin.ModelAdmin):
    """
    Admin interface for Page Sections
    """
    list_display = ['title', 'section_type', 'order', 'is_active', 'created']
    list_filter = ['section_type', 'is_active', 'created']
    search_fields = ['title', 'subtitle', 'content']
    list_editable = ['order', 'is_active']
    ordering = ['section_type', 'order']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('section_type', 'title', 'subtitle', 'content')
        }),
        ('Media', {
            'fields': ('image',),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('order', 'is_active')
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('section_type', 'order')




@admin.register(StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    """
    Admin interface for Staff Members
    """
    list_display = ['name', 'position', 'department', 'order', 'is_active', 'image_preview']
    list_filter = ['department', 'is_active', 'created']
    search_fields = ['name', 'position', 'department', 'bio']
    list_editable = ['order', 'is_active']
    ordering = ['order', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'position', 'department', 'bio')
        }),
        ('Contact & Media', {
            'fields': ('email', 'image')
        }),
        ('Settings', {
            'fields': ('order', 'is_active')
        }),
    )
    
    def image_preview(self, obj):
        """Display image preview in list view"""
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%; object-fit: cover;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = "Photo"


@admin.register(TimelineItem)
class TimelineItemAdmin(admin.ModelAdmin):
    """
    Admin interface for Timeline Items
    """
    list_display = ['year', 'title', 'order', 'is_active', 'created']
    list_filter = ['is_active', 'created']
    search_fields = ['year', 'title', 'description']
    list_editable = ['order', 'is_active']
    ordering = ['order', 'year']
    
    fieldsets = (
        ('Event Information', {
            'fields': ('year', 'title', 'description')
        }),
        ('Display Settings', {
            'fields': ('icon', 'order', 'is_active')
        }),
    )


@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    """
    Admin interface for Contact Information
    """
    list_display = ['contact_type', 'value_short', 'is_primary', 'order', 'is_active']
    list_filter = ['contact_type', 'is_primary', 'is_active', 'created']
    search_fields = ['value']
    list_editable = ['is_primary', 'order', 'is_active']
    ordering = ['contact_type', 'order']
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('contact_type', 'value')
        }),
        ('Settings', {
            'fields': ('is_primary', 'order', 'is_active')
        }),
    )
    
    def value_short(self, obj):
        """Display shortened value in list view"""
        return obj.value[:50] + "..." if len(obj.value) > 50 else obj.value
    value_short.short_description = "Value"


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    """
    Admin interface for FAQ Items
    """
    list_display = ['question_short', 'order', 'is_active', 'created']
    list_filter = ['is_active', 'created']
    search_fields = ['question', 'answer']
    list_editable = ['order', 'is_active']
    ordering = ['order', 'question']
    
    fieldsets = (
        ('FAQ Content', {
            'fields': ('question', 'answer')
        }),
        ('Settings', {
            'fields': ('order', 'is_active')
        }),
    )
    
    def question_short(self, obj):
        """Display shortened question in list view"""
        return obj.question[:60] + "..." if len(obj.question) > 60 else obj.question
    question_short.short_description = "Question"


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    """
    Admin interface for Features
    """
    list_display = ['title', 'icon', 'order', 'is_active', 'created']
    list_filter = ['is_active', 'created']
    search_fields = ['title', 'content']
    list_editable = ['order', 'is_active']
    ordering = ['order', 'title']
    
    fieldsets = (
        ('Feature Information', {
            'fields': ('title', 'content')
        }),
        ('Display Settings', {
            'fields': ('icon', 'icon_class', 'order', 'is_active')
        }),
        ('Link Settings', {
            'fields': ('link_url', 'link_text'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    """
    Admin interface for Testimonials
    """
    list_display = ['name', 'position', 'company', 'order', 'is_active', 'image_preview']
    list_filter = ['is_active', 'created']
    search_fields = ['name', 'position', 'company', 'quote']
    list_editable = ['order', 'is_active']
    ordering = ['order', 'name']
    
    fieldsets = (
        ('Person Information', {
            'fields': ('name', 'position', 'company')
        }),
        ('Testimonial Content', {
            'fields': ('quote', 'image')
        }),
        ('Settings', {
            'fields': ('order', 'is_active')
        }),
    )
    
    def image_preview(self, obj):
        """Display image preview in list view"""
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%; object-fit: cover;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = "Photo"


@admin.register(AboutPageConfig)
class AboutPageConfigAdmin(admin.ModelAdmin):
    """
    Admin interface for About Page Configuration (Singleton)
    """
    list_display = ['university_short_name', 'university_name', 'establishment_year', 'created']
    list_filter = ['created', 'modified']
    search_fields = ['university_name', 'university_short_name', 'mission', 'vision']
    
    fieldsets = (
        ('University Information', {
            'fields': ('university_name', 'university_short_name', 'establishment_year')
        }),
        ('University Description', {
            'fields': ('university_description', 'university_extended_description')
        }),
        ('Mission & Vision', {
            'fields': ('mission', 'vision')
        }),
        ('Page Configuration', {
            'fields': ('about_page_title', 'about_page_subtitle')
        }),
    )
    
    def has_add_permission(self, request):
        """Prevent adding multiple AboutPageConfig instances"""
        return not AboutPageConfig.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deleting the AboutPageConfig instance"""
        return False
    
    def changelist_view(self, request, extra_context=None):
        """Redirect to the single instance if it exists"""
        if AboutPageConfig.objects.exists():
            obj = AboutPageConfig.objects.first()
            return admin.ModelAdmin.change_view(
                self, request, str(obj.pk), extra_context
            )
        return super().changelist_view(request, extra_context)


@admin.register(AlumniStatistic)
class AlumniStatisticAdmin(admin.ModelAdmin):
    """
    Admin interface for Alumni Statistics
    """
    list_display = ['statistic_type', 'value', 'label', 'icon', 'icon_color', 'order', 'is_active']
    list_filter = ['statistic_type', 'icon_color', 'is_active', 'created']
    search_fields = ['label', 'value']
    list_editable = ['value', 'label', 'order', 'is_active']
    ordering = ['order', 'statistic_type']
    
    fieldsets = (
        ('Statistic Information', {
            'fields': ('statistic_type', 'value', 'label')
        }),
        ('Display Settings', {
            'fields': ('icon', 'icon_color', 'order', 'is_active')
        }),
    )


@admin.register(FooterLink)
class FooterLinkAdmin(admin.ModelAdmin):
    """
    Admin interface for Footer Links
    """
    list_display = ['title', 'section', 'url_preview', 'icon', 'open_in_new_tab', 'order', 'is_active']
    list_filter = ['section', 'open_in_new_tab', 'is_active', 'created']
    search_fields = ['title', 'url']
    list_editable = ['order', 'is_active']
    ordering = ['section', 'order', 'title']
    
    fieldsets = (
        ('Link Information', {
            'fields': ('title', 'url', 'section'),
            'description': 'Enter the link title and URL. For internal links, use Django URL names (e.g., "core:home") or paths (e.g., "/about/"). For external links, use full URLs (e.g., "https://example.com").'
        }),
        ('Display Settings', {
            'fields': ('icon', 'open_in_new_tab', 'order', 'is_active')
        }),
    )
    
    def url_preview(self, obj):
        """Display URL preview in list view"""
        try:
            url = obj.get_url()
            return format_html('<a href="{}" target="_blank">{}</a>', url, url[:50] + '...' if len(url) > 50 else url)
        except Exception as e:
            return format_html('<span style="color: red;">Error: {}</span>', str(e))
    url_preview.short_description = "URL"
    
    def get_queryset(self, request):
        return super().get_queryset(request).order_by('section', 'order')




# Customize admin site header and title
admin.site.site_header = "NORSU Alumni CMS"
admin.site.site_title = "CMS Admin"
admin.site.index_title = "Content Management System"