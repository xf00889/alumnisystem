from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models.contact import Address, ContactInfo
from .models.content import Post, Comment, Reaction
from .models.smtp_config import SMTPConfig
from .models.brevo_config import BrevoConfig
from .models.email_provider import EmailProvider

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

try:
    admin.site.register(SMTPConfig)
except admin.sites.AlreadyRegistered:
    pass

# Brevo Configuration Admin
@admin.register(BrevoConfig)
class BrevoConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'from_email', 'is_active', 'is_verified', 'last_tested', 'created_at']
    list_filter = ['is_active', 'is_verified', 'created_at']
    search_fields = ['name', 'from_email', 'api_key']
    readonly_fields = ['last_tested', 'test_result', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'from_email', 'from_name')
        }),
        ('API Configuration', {
            'fields': ('api_key', 'api_url')
        }),
        ('Status', {
            'fields': ('is_active', 'is_verified', 'last_tested', 'test_result')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['test_connection', 'test_send_email']
    
    def test_connection(self, request, queryset):
        """Test Brevo API connection"""
        for config in queryset:
            success, message = config.test_connection()
            if success:
                self.message_user(request, f"✓ {config.name}: {message}")
            else:
                self.message_user(request, f"✗ {config.name}: {message}", level='ERROR')
    
    def test_send_email(self, request, queryset):
        """Test Brevo API by sending a test email"""
        for config in queryset:
            success, message = config.test_connection(send_test_email=True)
            if success:
                self.message_user(request, f"✓ {config.name}: {message}")
            else:
                self.message_user(request, f"✗ {config.name}: {message}", level='ERROR')
    
    test_connection.short_description = "Test API Connection"
    test_send_email.short_description = "Test Send Email"

# Email Provider Admin
@admin.register(EmailProvider)
class EmailProviderAdmin(admin.ModelAdmin):
    list_display = ['provider_type', 'is_active', 'is_configured', 'emails_sent', 'last_used', 'created_at']
    list_filter = ['provider_type', 'is_active', 'created_at']
    readonly_fields = ['emails_sent', 'last_used', 'last_error', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Provider Configuration', {
            'fields': ('provider_type', 'is_active')
        }),
        ('Usage Statistics', {
            'fields': ('emails_sent', 'last_used', 'last_error')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_provider', 'deactivate_provider', 'reset_statistics']
    
    def is_configured(self, obj):
        """Show if the provider has a valid configuration"""
        return obj.is_configured()
    is_configured.boolean = True
    is_configured.short_description = 'Configured'
    
    def activate_provider(self, request, queryset):
        """Activate selected providers"""
        for provider in queryset:
            provider.is_active = True
            provider.save()
            self.message_user(request, f"✓ Activated {provider.get_provider_type_display()}")
    
    def deactivate_provider(self, request, queryset):
        """Deactivate selected providers"""
        for provider in queryset:
            provider.is_active = False
            provider.save()
            self.message_user(request, f"✓ Deactivated {provider.get_provider_type_display()}")
    
    def reset_statistics(self, request, queryset):
        """Reset usage statistics"""
        for provider in queryset:
            provider.emails_sent = 0
            provider.last_used = None
            provider.last_error = ''
            provider.save()
            self.message_user(request, f"✓ Reset statistics for {provider.get_provider_type_display()}")
    
    activate_provider.short_description = "Activate Provider"
    deactivate_provider.short_description = "Deactivate Provider"
    reset_statistics.short_description = "Reset Statistics"