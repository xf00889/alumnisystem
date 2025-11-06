from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils import timezone
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Admin interface for AuditLog model
    """
    list_display = [
        'timestamp', 'action', 'model_name', 'app_label', 
        'username', 'object_repr_display', 'ip_address'
    ]
    list_filter = [
        'action', 'app_label', 'model_name', 'timestamp', 'user'
    ]
    search_fields = [
        'username', 'message', 'model_name', 'app_label', 
        'ip_address', 'request_path'
    ]
    readonly_fields = [
        'content_type', 'object_id', 'action', 'model_name', 'app_label',
        'user', 'username', 'old_values', 'new_values', 'changed_fields',
        'ip_address', 'user_agent', 'request_path', 'message', 'timestamp'
    ]
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    
    fieldsets = (
        ('Action Information', {
            'fields': ('timestamp', 'action', 'model_name', 'app_label', 'message')
        }),
        ('Object Information', {
            'fields': ('content_type', 'object_id', 'object_repr_display')
        }),
        ('User Information', {
            'fields': ('user', 'username', 'ip_address', 'user_agent', 'request_path')
        }),
        ('Change Details', {
            'fields': ('old_values', 'new_values', 'changed_fields'),
            'classes': ('collapse',)
        }),
    )
    
    def object_repr_display(self, obj):
        """Display object representation"""
        return obj.object_repr
    object_repr_display.short_description = 'Object'
    
    def has_add_permission(self, request):
        """Disable manual creation of audit logs"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Make audit logs read-only"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Allow deletion of audit logs (for cleanup)"""
        return request.user.is_superuser
    
    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('user', 'content_type')


# Original log viewer admin (for backwards compatibility)
class LogViewerAdmin(admin.ModelAdmin):
    """
    Custom admin interface for log viewer
    """
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['log_viewer_url'] = reverse('log_viewer:log_list')
        return super().changelist_view(request, extra_context)

# Add a custom admin link
def log_viewer_link(request):
    """Add link to log viewer in admin"""
    from django.contrib.admin.sites import site
    # This will be added via admin template customization
    pass
