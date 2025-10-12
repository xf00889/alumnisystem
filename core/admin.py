from django.contrib import admin
from django.utils.html import format_html
from .models.page_content import PageSection, Testimonial, StaffMember, SiteConfiguration
from .models.contact import Address, ContactInfo
from .models.content import Post, Comment, Reaction

@admin.register(PageSection)
class PageSectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'section_type', 'title', 'is_active', 'order', 'updated_at')
    list_filter = ('section_type', 'is_active')
    search_fields = ('name', 'title', 'content')
    ordering = ('order', 'name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'section_type', 'title', 'subtitle', 'content')
        }),
        ('Media', {
            'fields': ('image', 'background_image')
        }),
        ('Settings', {
            'fields': ('is_active', 'order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'company', 'graduation_year', 'is_featured', 'is_active', 'order')
    list_filter = ('is_featured', 'is_active', 'graduation_year')
    search_fields = ('name', 'position', 'company', 'quote')
    ordering = ('-is_featured', 'order', '-created_at')
    readonly_fields = ('created_at', 'updated_at', 'image_preview')
    fieldsets = (
        (None, {
            'fields': ('name', 'position', 'company', 'graduation_year', 'quote')
        }),
        ('Media', {
            'fields': ('image', 'image_preview')
        }),
        ('Settings', {
            'fields': ('is_featured', 'is_active', 'order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 300px;" />', obj.image.url)
        return "No image"
    image_preview.short_description = 'Image Preview'

@admin.register(StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'position', 'staff_type', 'department', 'email', 'is_active', 'order')
    list_filter = ('staff_type', 'is_active', 'department')
    search_fields = ('name', 'position', 'department', 'bio', 'email')
    ordering = ('staff_type', 'order', 'name')
    readonly_fields = ('created_at', 'updated_at', 'image_preview')
    fieldsets = (
        (None, {
            'fields': ('name', 'position', 'staff_type', 'department', 'bio')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone')
        }),
        ('Media', {
            'fields': ('image', 'image_preview')
        }),
        ('Settings', {
            'fields': ('is_active', 'order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px; max-width: 300px;" />', obj.image.url)
        return "No image"
    image_preview.short_description = 'Image Preview'

@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Site Information', {
            'fields': ('site_name', 'site_tagline', 'primary_color', 'secondary_color')
        }),
        ('Contact Information', {
            'fields': ('contact_email', 'contact_phone', 'contact_address')
        }),
        ('Social Media', {
            'fields': ('facebook_url', 'twitter_url', 'instagram_url', 'linkedin_url', 'youtube_url')
        }),
        ('Statistics Overrides', {
            'fields': ('alumni_count_override', 'groups_count_override', 'jobs_count_override'),
            'description': 'Leave blank to use actual counts from database'
        }),
        ('Footer', {
            'fields': ('footer_text', 'copyright_text')
        }),
        ('SEO', {
            'fields': ('meta_description', 'meta_keywords')
        }),
        ('Maintenance', {
            'fields': ('maintenance_mode', 'maintenance_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow adding if no configuration exists
        return not SiteConfiguration.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the configuration
        return False

# Register existing models if they aren't already registered
try:
    admin.site.register(Address)
except admin.sites.AlreadyRegistered:
    pass

try:
    admin.site.register(ContactInfo)
except admin.sites.AlreadyRegistered:
    pass

try:
    admin.site.register(Post)
except admin.sites.AlreadyRegistered:
    pass

try:
    admin.site.register(Comment)
except admin.sites.AlreadyRegistered:
    pass

try:
    admin.site.register(Reaction)
except admin.sites.AlreadyRegistered:
    pass