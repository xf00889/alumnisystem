from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    SiteConfig, StaffMember, 
    TimelineItem, ContactInfo, FAQ, Feature, Testimonial,
    AlumniStatistic, FooterLink,
    NORSUCampus, NORSUOfficial, NORSUVMGOHistory
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
        ('Hero Section', {
            'fields': (
                'hero_headline',
                'hero_subheadline',
                'hero_background_image',
                'hero_primary_cta_text',
                'hero_secondary_cta_text',
                'hero_microcopy',
                'hero_alumni_count',
                'hero_opportunities_count',
                'hero_countries_count',
                'hero_variant',
            ),
            'description': 'Configure the hero section messaging, CTAs, and social proof elements'
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


@admin.register(NORSUCampus)
class NORSUCampusAdmin(admin.ModelAdmin):
    """
    Admin interface for NORSU Campuses
    """
    list_display = ['name', 'location', 'order', 'is_active', 'image_preview', 'created']
    list_filter = ['is_active', 'created']
    search_fields = ['name', 'location', 'description']
    list_editable = ['order', 'is_active']
    ordering = ['order', 'name']
    
    fieldsets = (
        ('Campus Information', {
            'fields': ('name', 'location', 'description')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Settings', {
            'fields': ('order', 'is_active')
        }),
    )
    
    def image_preview(self, obj):
        """Display image preview in list view"""
        if obj.image:
            return format_html(
                '<img src="{}" width="80" height="50" style="object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = "Preview"


@admin.register(NORSUOfficial)
class NORSUOfficialAdmin(admin.ModelAdmin):
    """
    Admin interface for NORSU Officials
    """
    list_display = ['name', 'position', 'position_level_display', 'department', 'order', 'is_active', 'image_preview']
    list_filter = ['position_level', 'is_active', 'created']
    search_fields = ['name', 'position', 'department', 'bio']
    list_editable = ['order', 'is_active']
    ordering = ['position_level', 'order', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'position', 'position_level', 'department', 'bio')
        }),
        ('Contact & Media', {
            'fields': ('email', 'phone', 'image')
        }),
        ('Settings', {
            'fields': ('order', 'is_active')
        }),
    )
    
    def position_level_display(self, obj):
        """Display position level with color coding"""
        colors = {
            1: '#dc3545',  # Red for President
            2: '#fd7e14',  # Orange for VP
            3: '#ffc107',  # Yellow for Dean
            4: '#28a745',  # Green for Associate Dean
            5: '#17a2b8',  # Cyan for Director
            6: '#6c757d',  # Gray for Department Head
            7: '#6c757d',  # Gray for Other
        }
        color = colors.get(obj.position_level, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_position_level_display()
        )
    position_level_display.short_description = "Level"
    
    def image_preview(self, obj):
        """Display image preview in list view"""
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%; object-fit: cover;" />',
                obj.image.url
            )
        return "No Image"
    image_preview.short_description = "Photo"


@admin.register(NORSUVMGOHistory)
class NORSUVMGOHistoryAdmin(admin.ModelAdmin):
    """
    Admin interface for NORSU VMGO & History (Singleton)
    """
    list_display = ['__str__', 'is_active', 'establishment_year', 'university_status_year', 'created']
    list_filter = ['is_active', 'show_on_homepage', 'show_history_on_homepage', 'created', 'modified']
    search_fields = ['section_title', 'about_content', 'vision', 'mission', 'goals', 'core_values', 'history_brief', 'history_full']
    
    fieldsets = (
        ('Section Configuration', {
            'fields': ('section_title', 'is_active'),
            'description': 'Configure the main section title and visibility'
        }),
        ('About NORSU', {
            'fields': ('about_title', 'about_content'),
            'description': 'Introduction text about NORSU'
        }),
        ('Vision & Mission', {
            'fields': (
                ('vision_title', 'mission_title'),
                'vision',
                'mission'
            ),
            'description': 'NORSU Vision and Mission statements'
        }),
        ('Goals & Values', {
            'fields': (
                'goals_title',
                'goals',
                'values_title',
                'core_values',
                'quality_policy'
            ),
            'description': 'Strategic goals, core values, and quality policy'
        }),
        ('History', {
            'fields': ('establishment_year', 'university_status_year', 'history_brief', 'history_full'),
            'description': 'Historical information about NORSU'
        }),
        ('Legacy Display Settings', {
            'fields': ('show_on_homepage', 'show_history_on_homepage'),
            'classes': ('collapse',),
            'description': 'Legacy settings (use is_active instead)'
        }),
    )
    
    def has_add_permission(self, request):
        """Prevent adding multiple NORSUVMGOHistory instances"""
        return not NORSUVMGOHistory.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deleting the NORSUVMGOHistory instance"""
        return False
    
    def changelist_view(self, request, extra_context=None):
        """Redirect to the single instance if it exists"""
        if NORSUVMGOHistory.objects.exists():
            obj = NORSUVMGOHistory.objects.first()
            return admin.ModelAdmin.change_view(
                self, request, str(obj.pk), extra_context
            )
        return super().changelist_view(request, extra_context)


# Customize admin site header and title
admin.site.site_header = "NORSU Alumni Administration"
admin.site.site_title = "NORSU Alumni Admin"
admin.site.index_title = "Site Administration"