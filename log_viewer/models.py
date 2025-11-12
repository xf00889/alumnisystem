from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import json

User = get_user_model()


class AuditLog(models.Model):
    """
    Model to store all CRUD operations (Create, Read, Update, Delete) 
    across all models in the system.
    """
    ACTION_CHOICES = (
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('VIEW', 'View'),
    )
    
    # Generic relation to any model
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Action details
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100, db_index=True)
    app_label = models.CharField(max_length=50, db_index=True)
    
    # User information
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    username = models.CharField(max_length=150, blank=True, null=True)
    
    # Data changes
    old_values = models.JSONField(null=True, blank=True, help_text="Previous field values (for updates)")
    new_values = models.JSONField(null=True, blank=True, help_text="New field values (for creates/updates)")
    changed_fields = models.JSONField(null=True, blank=True, help_text="List of changed field names (for updates)")
    
    # Additional context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    request_path = models.CharField(max_length=500, blank=True, null=True)
    message = models.TextField(blank=True, help_text="Human-readable description of the action")
    
    # Timestamp
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp', 'action']),
            models.Index(fields=['model_name', 'app_label']),
            models.Index(fields=['user', 'timestamp']),
        ]
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
    
    def __str__(self):
        return f"{self.action} {self.model_name} #{self.object_id} by {self.username or 'Anonymous'}"
    
    @property
    def object_repr(self):
        """Get string representation of the related object"""
        try:
            obj = self.content_object
            if obj:
                return str(obj)
        except:
            pass
        return f"{self.model_name} #{self.object_id}"
    
    def get_changes_summary(self):
        """Get a summary of what changed"""
        if self.action == 'CREATE':
            return "Object created"
        elif self.action == 'UPDATE':
            if self.changed_fields:
                return f"Fields changed: {', '.join(self.changed_fields)}"
            return "Object updated"
        elif self.action == 'DELETE':
            return "Object deleted"
        return "Action performed"


class LogRetentionPolicy(models.Model):
    """Configuration for log retention policies"""
    
    LOG_TYPE_CHOICES = [
        ('audit', 'Audit Logs'),
        ('file', 'File Logs'),
    ]
    
    EXPORT_FORMAT_CHOICES = [
        ('csv', 'CSV'),
        ('pdf', 'PDF'),
        ('both', 'Both CSV and PDF'),
    ]
    
    log_type = models.CharField(
        max_length=10, 
        choices=LOG_TYPE_CHOICES, 
        unique=True,
        help_text="Type of logs this policy applies to"
    )
    enabled = models.BooleanField(
        default=False,
        help_text="Whether this retention policy is active"
    )
    retention_days = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(3650)],
        help_text="Number of days to retain logs before deletion (1-3650)"
    )
    export_before_delete = models.BooleanField(
        default=True,
        help_text="Export logs to archive before deletion"
    )
    export_format = models.CharField(
        max_length=10, 
        choices=EXPORT_FORMAT_CHOICES, 
        default='csv',
        help_text="Format for exported archive files"
    )
    archive_path = models.CharField(
        max_length=500,
        default='logs/archives',
        help_text="Path relative to MEDIA_ROOT for storing archives"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Log Retention Policy'
        verbose_name_plural = 'Log Retention Policies'
        ordering = ['log_type']
    
    def __str__(self):
        status = "Enabled" if self.enabled else "Disabled"
        return f"{self.get_log_type_display()} - {self.retention_days} days ({status})"


class LogCleanupSchedule(models.Model):
    """Configuration for automated cleanup scheduling"""
    
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    DAY_OF_WEEK_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    enabled = models.BooleanField(
        default=False,
        help_text="Whether automatic cleanup is enabled"
    )
    frequency = models.CharField(
        max_length=10, 
        choices=FREQUENCY_CHOICES,
        help_text="How often to run cleanup"
    )
    execution_time = models.TimeField(
        help_text="Time of day to run cleanup (24-hour format)"
    )
    day_of_week = models.IntegerField(
        choices=DAY_OF_WEEK_CHOICES, 
        null=True, 
        blank=True,
        help_text="For weekly frequency - which day to run"
    )
    day_of_month = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(28)],
        help_text="For monthly frequency - which day to run (1-28)"
    )
    last_run = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When cleanup was last executed"
    )
    next_run = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When cleanup is scheduled to run next"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Log Cleanup Schedule'
        verbose_name_plural = 'Log Cleanup Schedules'
    
    def __str__(self):
        status = "Enabled" if self.enabled else "Disabled"
        freq_display = self.get_frequency_display()
        return f"{freq_display} at {self.execution_time} ({status})"


class LogOperationHistory(models.Model):
    """History of log cleanup operations"""
    
    OPERATION_TYPE_CHOICES = [
        ('scheduled', 'Scheduled Cleanup'),
        ('manual', 'Manual Cleanup'),
    ]
    
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('partial', 'Partial Success'),
        ('failed', 'Failed'),
    ]
    
    operation_type = models.CharField(
        max_length=10, 
        choices=OPERATION_TYPE_CHOICES,
        help_text="Whether this was a scheduled or manual operation"
    )
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES,
        help_text="Overall status of the operation"
    )
    started_at = models.DateTimeField(
        help_text="When the operation started"
    )
    completed_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When the operation completed"
    )
    
    # Metrics
    audit_logs_processed = models.IntegerField(
        default=0,
        help_text="Number of audit log records processed"
    )
    audit_logs_deleted = models.IntegerField(
        default=0,
        help_text="Number of audit log records deleted"
    )
    file_logs_processed = models.IntegerField(
        default=0,
        help_text="Number of file log entries processed"
    )
    file_logs_deleted = models.IntegerField(
        default=0,
        help_text="Number of file log entries deleted"
    )
    archives_created = models.IntegerField(
        default=0,
        help_text="Number of archive files created"
    )
    
    # Details
    error_message = models.TextField(
        blank=True,
        help_text="Error details if operation failed"
    )
    archive_files = models.JSONField(
        default=list, 
        help_text="List of created archive files"
    )
    
    # User (for manual operations)
    triggered_by = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='log_operations',
        help_text="User who triggered manual operation"
    )
    
    class Meta:
        verbose_name = 'Log Operation History'
        verbose_name_plural = 'Log Operation History'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['-started_at']),
            models.Index(fields=['status', '-started_at']),
        ]
    
    def __str__(self):
        return f"{self.get_operation_type_display()} - {self.get_status_display()} ({self.started_at})"
    
    @property
    def duration(self):
        """Calculate operation duration"""
        if self.completed_at and self.started_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds()
        return None
    
    @property
    def total_processed(self):
        """Total records processed"""
        return self.audit_logs_processed + self.file_logs_processed
    
    @property
    def total_deleted(self):
        """Total records deleted"""
        return self.audit_logs_deleted + self.file_logs_deleted


class ArchiveStorageConfig(models.Model):
    """Configuration for archive storage management"""
    
    max_storage_gb = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=10.0,
        validators=[MinValueValidator(0.1)],
        help_text="Maximum storage size for archives in GB"
    )
    warning_threshold_percent = models.IntegerField(
        default=80,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Percentage at which to show warning (1-100)"
    )
    critical_threshold_percent = models.IntegerField(
        default=95,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text="Percentage at which to pause archival (1-100)"
    )
    current_size_gb = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0.0,
        validators=[MinValueValidator(0)],
        help_text="Current archive storage size in GB"
    )
    last_size_check = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When storage size was last calculated"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Archive Storage Configuration'
        verbose_name_plural = 'Archive Storage Configuration'
    
    def __str__(self):
        return f"Archive Storage: {self.current_size_gb} GB / {self.max_storage_gb} GB"
    
    @property
    def usage_percent(self):
        """Calculate current storage usage percentage"""
        if self.max_storage_gb > 0:
            return (float(self.current_size_gb) / float(self.max_storage_gb)) * 100
        return 0
    
    @property
    def is_warning(self):
        """Check if storage is at warning threshold"""
        return self.usage_percent >= self.warning_threshold_percent
    
    @property
    def is_critical(self):
        """Check if storage is at critical threshold"""
        return self.usage_percent >= self.critical_threshold_percent
    
    @property
    def status(self):
        """Get storage status"""
        if self.is_critical:
            return 'critical'
        elif self.is_warning:
            return 'warning'
        return 'normal'
