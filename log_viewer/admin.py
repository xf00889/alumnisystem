from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import HttpResponse
from .models import (
    AuditLog, 
    LogRetentionPolicy, 
    LogCleanupSchedule, 
    LogOperationHistory, 
    ArchiveStorageConfig
)
import csv
import os
from decimal import Decimal


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


@admin.register(LogRetentionPolicy)
class LogRetentionPolicyAdmin(admin.ModelAdmin):
    """
    Admin interface for Log Retention Policy configuration
    """
    list_display = [
        'log_type_display', 
        'enabled_status', 
        'retention_days', 
        'export_format',
        'export_before_delete',
        'updated_at'
    ]
    list_filter = ['enabled', 'log_type', 'export_format']
    search_fields = ['log_type', 'archive_path']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['toggle_enabled_status']
    
    fieldsets = (
        ('Policy Configuration', {
            'fields': ('log_type', 'enabled', 'retention_days')
        }),
        ('Export Settings', {
            'fields': ('export_before_delete', 'export_format', 'archive_path')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def log_type_display(self, obj):
        """Display log type with icon"""
        icons = {
            'audit': '📊',
            'file': '📄'
        }
        icon = icons.get(obj.log_type, '📋')
        return format_html(
            '<span style="font-size: 16px;">{}</span> {}',
            icon,
            obj.get_log_type_display()
        )
    log_type_display.short_description = 'Log Type'
    log_type_display.admin_order_field = 'log_type'
    
    def enabled_status(self, obj):
        """Display enabled status with visual indicator"""
        if obj.enabled:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✓ Enabled</span>'
            )
        else:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">✗ Disabled</span>'
            )
    enabled_status.short_description = 'Status'
    enabled_status.admin_order_field = 'enabled'
    
    def toggle_enabled_status(self, request, queryset):
        """Quick action to toggle enabled status"""
        for policy in queryset:
            policy.enabled = not policy.enabled
            policy.save()
        
        count = queryset.count()
        self.message_user(
            request,
            f'Successfully toggled status for {count} retention {"policy" if count == 1 else "policies"}.'
        )
    toggle_enabled_status.short_description = 'Toggle enabled/disabled status'
    
    def get_form(self, request, obj=None, **kwargs):
        """Add custom validation to the form"""
        form = super().get_form(request, obj, **kwargs)
        
        # Add help text for retention_days
        if 'retention_days' in form.base_fields:
            form.base_fields['retention_days'].help_text = (
                'Number of days to retain logs before deletion (minimum: 1, maximum: 3650)'
            )
        
        return form
    
    def save_model(self, request, obj, form, change):
        """Custom validation on save"""
        # Validate retention_days
        if obj.retention_days < 1 or obj.retention_days > 3650:
            raise ValidationError(
                'Retention days must be between 1 and 3650 days.'
            )
        
        # Validate archive path
        if obj.archive_path:
            obj.archive_path = obj.archive_path.strip()
        
        super().save_model(request, obj, form, change)


@admin.register(LogCleanupSchedule)
class LogCleanupScheduleAdmin(admin.ModelAdmin):
    """
    Admin interface for Log Cleanup Schedule configuration
    """
    list_display = [
        'schedule_display',
        'enabled_status',
        'frequency',
        'execution_time',
        'last_run_display',
        'next_run_display'
    ]
    list_filter = ['enabled', 'frequency']
    readonly_fields = ['last_run', 'next_run', 'created_at', 'updated_at']
    actions = ['trigger_manual_cleanup']
    
    fieldsets = (
        ('Schedule Configuration', {
            'fields': ('enabled', 'frequency', 'execution_time'),
            'description': 'Configure when automatic log cleanup should run'
        }),
        ('Frequency Details', {
            'fields': ('day_of_week', 'day_of_month'),
            'description': 'Additional settings based on frequency (weekly/monthly)'
        }),
        ('Execution Status', {
            'fields': ('last_run', 'next_run'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def schedule_display(self, obj):
        """Display schedule summary"""
        freq = obj.get_frequency_display()
        time = obj.execution_time.strftime('%H:%M')
        
        if obj.frequency == 'weekly' and obj.day_of_week is not None:
            day = obj.get_day_of_week_display()
            return format_html(
                '<strong>{}</strong> on {} at {}',
                freq, day, time
            )
        elif obj.frequency == 'monthly' and obj.day_of_month:
            return format_html(
                '<strong>{}</strong> on day {} at {}',
                freq, obj.day_of_month, time
            )
        else:
            return format_html(
                '<strong>{}</strong> at {}',
                freq, time
            )
    schedule_display.short_description = 'Schedule'
    
    def enabled_status(self, obj):
        """Display enabled status with visual indicator"""
        if obj.enabled:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✓ Active</span>'
            )
        else:
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">✗ Inactive</span>'
            )
    enabled_status.short_description = 'Status'
    enabled_status.admin_order_field = 'enabled'
    
    def last_run_display(self, obj):
        """Display last run time"""
        if obj.last_run:
            return format_html(
                '<span title="{}">{}</span>',
                obj.last_run.strftime('%Y-%m-%d %H:%M:%S'),
                obj.last_run.strftime('%b %d, %Y %H:%M')
            )
        return format_html('<span style="color: #6c757d;">Never</span>')
    last_run_display.short_description = 'Last Run'
    last_run_display.admin_order_field = 'last_run'
    
    def next_run_display(self, obj):
        """Display next scheduled run prominently"""
        if obj.next_run:
            now = timezone.now()
            if obj.next_run > now:
                return format_html(
                    '<span style="color: #007bff; font-weight: bold;" title="{}">{}</span>',
                    obj.next_run.strftime('%Y-%m-%d %H:%M:%S'),
                    obj.next_run.strftime('%b %d, %Y %H:%M')
                )
            else:
                return format_html(
                    '<span style="color: #ffc107; font-weight: bold;" title="{}">⚠ Overdue: {}</span>',
                    obj.next_run.strftime('%Y-%m-%d %H:%M:%S'),
                    obj.next_run.strftime('%b %d, %Y %H:%M')
                )
        return format_html('<span style="color: #6c757d;">Not scheduled</span>')
    next_run_display.short_description = 'Next Run'
    next_run_display.admin_order_field = 'next_run'
    
    def trigger_manual_cleanup(self, request, queryset):
        """Custom admin action to manually trigger cleanup"""
        # Import here to avoid circular imports
        from .services import LogManagementService
        
        try:
            service = LogManagementService()
            operation = service.execute_cleanup(
                triggered_by=request.user,
                operation_type='manual'
            )
            
            self.message_user(
                request,
                format_html(
                    'Manual cleanup triggered successfully. '
                    'Processed {} records. '
                    '<a href="{}">View operation details</a>',
                    operation.total_processed,
                    reverse('admin:log_viewer_logoperationhistory_change', args=[operation.id])
                )
            )
        except Exception as e:
            self.message_user(
                request,
                f'Failed to trigger cleanup: {str(e)}',
                level='error'
            )
    trigger_manual_cleanup.short_description = 'Trigger manual cleanup now'
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize form with conditional fields"""
        form = super().get_form(request, obj, **kwargs)
        
        # Add JavaScript for conditional field display
        if 'frequency' in form.base_fields:
            form.base_fields['frequency'].help_text = (
                'Select how often cleanup should run'
            )
        
        return form
    
    def save_model(self, request, obj, form, change):
        """Custom validation on save"""
        # Validate frequency-specific fields
        if obj.frequency == 'weekly' and obj.day_of_week is None:
            raise ValidationError(
                'Day of week is required for weekly frequency.'
            )
        
        if obj.frequency == 'monthly' and not obj.day_of_month:
            raise ValidationError(
                'Day of month is required for monthly frequency.'
            )
        
        # Clear irrelevant fields
        if obj.frequency == 'daily':
            obj.day_of_week = None
            obj.day_of_month = None
        elif obj.frequency == 'weekly':
            obj.day_of_month = None
        elif obj.frequency == 'monthly':
            obj.day_of_week = None
        
        # Calculate next run if enabled
        if obj.enabled and not obj.next_run:
            from .services import LogManagementService
            service = LogManagementService()
            obj.next_run = service.calculate_next_run_time(obj)
        
        super().save_model(request, obj, form, change)


@admin.register(LogOperationHistory)
class LogOperationHistoryAdmin(admin.ModelAdmin):
    """
    Admin interface for Log Operation History (read-only)
    """
    list_display = [
        'started_at_display',
        'operation_type',
        'status_display',
        'total_processed',
        'total_deleted',
        'archives_created',
        'duration_display',
        'triggered_by'
    ]
    list_filter = [
        'status',
        'operation_type',
        ('started_at', admin.DateFieldListFilter),
    ]
    search_fields = ['error_message', 'triggered_by__username']
    readonly_fields = [
        'operation_type', 'status', 'started_at', 'completed_at',
        'audit_logs_processed', 'audit_logs_deleted',
        'file_logs_processed', 'file_logs_deleted',
        'archives_created', 'error_message', 'archive_files',
        'triggered_by', 'duration_display', 'total_processed', 'total_deleted'
    ]
    date_hierarchy = 'started_at'
    actions = ['export_to_csv']
    
    fieldsets = (
        ('Operation Information', {
            'fields': (
                'operation_type', 'status', 'started_at', 
                'completed_at', 'duration_display', 'triggered_by'
            )
        }),
        ('Audit Log Metrics', {
            'fields': ('audit_logs_processed', 'audit_logs_deleted')
        }),
        ('File Log Metrics', {
            'fields': ('file_logs_processed', 'file_logs_deleted')
        }),
        ('Archive Information', {
            'fields': ('archives_created', 'archive_files')
        }),
        ('Error Details', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
    )
    
    def started_at_display(self, obj):
        """Display start time"""
        return obj.started_at.strftime('%Y-%m-%d %H:%M:%S')
    started_at_display.short_description = 'Started At'
    started_at_display.admin_order_field = 'started_at'
    
    def status_display(self, obj):
        """Display status with color coding"""
        colors = {
            'success': '#28a745',
            'partial': '#ffc107',
            'failed': '#dc3545'
        }
        icons = {
            'success': '✓',
            'partial': '⚠',
            'failed': '✗'
        }
        color = colors.get(obj.status, '#6c757d')
        icon = icons.get(obj.status, '•')
        
        html = format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_status_display()
        )
        
        # Add error message tooltip for failed operations
        if obj.status == 'failed' and obj.error_message:
            html = format_html(
                '<span style="color: {}; font-weight: bold;" title="{}">{} {}</span>',
                color, obj.error_message[:100], icon, obj.get_status_display()
            )
        
        return html
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'status'
    
    def duration_display(self, obj):
        """Display operation duration"""
        if obj.duration:
            minutes = int(obj.duration // 60)
            seconds = int(obj.duration % 60)
            if minutes > 0:
                return f'{minutes}m {seconds}s'
            return f'{seconds}s'
        return '-'
    duration_display.short_description = 'Duration'
    
    def export_to_csv(self, request, queryset):
        """Export operation history to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="log_operation_history.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Started At', 'Completed At', 'Operation Type', 'Status',
            'Audit Logs Processed', 'Audit Logs Deleted',
            'File Logs Processed', 'File Logs Deleted',
            'Archives Created', 'Duration (seconds)', 'Triggered By', 'Error Message'
        ])
        
        for obj in queryset:
            writer.writerow([
                obj.started_at.strftime('%Y-%m-%d %H:%M:%S'),
                obj.completed_at.strftime('%Y-%m-%d %H:%M:%S') if obj.completed_at else '',
                obj.get_operation_type_display(),
                obj.get_status_display(),
                obj.audit_logs_processed,
                obj.audit_logs_deleted,
                obj.file_logs_processed,
                obj.file_logs_deleted,
                obj.archives_created,
                obj.duration if obj.duration else '',
                obj.triggered_by.username if obj.triggered_by else 'System',
                obj.error_message
            ])
        
        return response
    export_to_csv.short_description = 'Export selected to CSV'
    
    def has_add_permission(self, request):
        """Disable manual creation"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Make read-only"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Allow superusers to delete old history"""
        return request.user.is_superuser


@admin.register(ArchiveStorageConfig)
class ArchiveStorageConfigAdmin(admin.ModelAdmin):
    """
    Admin interface for Archive Storage Configuration
    """
    list_display = [
        'storage_display',
        'usage_display',
        'status_display',
        'last_size_check'
    ]
    readonly_fields = [
        'current_size_gb', 
        'last_size_check', 
        'usage_percent_display',
        'status_display_detailed',
        'created_at', 
        'updated_at'
    ]
    actions = ['recalculate_storage_size']
    
    fieldsets = (
        ('Storage Limits', {
            'fields': ('max_storage_gb',),
            'description': 'Configure maximum storage size for log archives'
        }),
        ('Threshold Settings', {
            'fields': ('warning_threshold_percent', 'critical_threshold_percent'),
            'description': 'Set warning and critical thresholds as percentages'
        }),
        ('Current Usage', {
            'fields': (
                'current_size_gb', 
                'usage_percent_display',
                'status_display_detailed',
                'last_size_check'
            ),
            'description': 'Current storage usage information'
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def storage_display(self, obj):
        """Display storage with icon"""
        return format_html(
            '<span style="font-size: 16px;">💾</span> Archive Storage'
        )
    storage_display.short_description = 'Configuration'
    
    def usage_display(self, obj):
        """Display storage usage with progress bar"""
        percent = obj.usage_percent
        
        # Determine color based on thresholds
        if percent >= obj.critical_threshold_percent:
            color = '#dc3545'  # Red
        elif percent >= obj.warning_threshold_percent:
            color = '#ffc107'  # Yellow
        else:
            color = '#28a745'  # Green
        
        return format_html(
            '<div style="width: 200px; background-color: #e9ecef; border-radius: 4px; overflow: hidden;">'
            '<div style="width: {}%; background-color: {}; height: 20px; text-align: center; color: white; font-size: 11px; line-height: 20px;">'
            '{:.1f}%'
            '</div>'
            '</div>'
            '<div style="font-size: 11px; color: #6c757d; margin-top: 2px;">'
            '{:.2f} GB / {:.2f} GB'
            '</div>',
            min(percent, 100), color, percent,
            obj.current_size_gb, obj.max_storage_gb
        )
    usage_display.short_description = 'Usage'
    
    def usage_percent_display(self, obj):
        """Display usage percentage"""
        return f'{obj.usage_percent:.2f}%'
    usage_percent_display.short_description = 'Usage Percentage'
    
    def status_display(self, obj):
        """Display status indicator"""
        status = obj.status
        
        if status == 'critical':
            return format_html(
                '<span style="color: #dc3545; font-weight: bold;">🔴 CRITICAL</span>'
            )
        elif status == 'warning':
            return format_html(
                '<span style="color: #ffc107; font-weight: bold;">⚠ WARNING</span>'
            )
        else:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✓ Normal</span>'
            )
    status_display.short_description = 'Status'
    
    def status_display_detailed(self, obj):
        """Display detailed status with explanation"""
        status = obj.status
        percent = obj.usage_percent
        
        if status == 'critical':
            return format_html(
                '<div style="padding: 10px; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px; color: #721c24;">'
                '<strong>🔴 CRITICAL:</strong> Storage usage is at {:.1f}%, exceeding the critical threshold of {}%. '
                'Automatic archival is paused to prevent storage overflow.'
                '</div>',
                percent, obj.critical_threshold_percent
            )
        elif status == 'warning':
            return format_html(
                '<div style="padding: 10px; background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 4px; color: #856404;">'
                '<strong>⚠ WARNING:</strong> Storage usage is at {:.1f}%, exceeding the warning threshold of {}%. '
                'Consider increasing storage limit or cleaning up old archives.'
                '</div>',
                percent, obj.warning_threshold_percent
            )
        else:
            return format_html(
                '<div style="padding: 10px; background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px; color: #155724;">'
                '<strong>✓ Normal:</strong> Storage usage is at {:.1f}%, within acceptable limits.'
                '</div>',
                percent
            )
    status_display_detailed.short_description = 'Status Details'
    
    def recalculate_storage_size(self, request, queryset):
        """Recalculate storage size for selected configurations"""
        from django.conf import settings
        
        for config in queryset:
            try:
                # Get archive path from retention policies
                archive_paths = LogRetentionPolicy.objects.values_list('archive_path', flat=True).distinct()
                
                total_size = 0
                for archive_path in archive_paths:
                    full_path = os.path.join(settings.MEDIA_ROOT, archive_path)
                    if os.path.exists(full_path):
                        for dirpath, dirnames, filenames in os.walk(full_path):
                            for filename in filenames:
                                filepath = os.path.join(dirpath, filename)
                                if os.path.exists(filepath):
                                    total_size += os.path.getsize(filepath)
                
                # Convert bytes to GB
                config.current_size_gb = Decimal(total_size / (1024 ** 3))
                config.last_size_check = timezone.now()
                config.save()
                
                self.message_user(
                    request,
                    f'Storage size recalculated: {config.current_size_gb:.2f} GB'
                )
            except Exception as e:
                self.message_user(
                    request,
                    f'Failed to recalculate storage: {str(e)}',
                    level='error'
                )
    recalculate_storage_size.short_description = 'Recalculate storage size'
    
    def save_model(self, request, obj, form, change):
        """Custom validation on save"""
        # Validate thresholds
        if obj.warning_threshold_percent >= obj.critical_threshold_percent:
            raise ValidationError(
                'Warning threshold must be less than critical threshold.'
            )
        
        super().save_model(request, obj, form, change)
