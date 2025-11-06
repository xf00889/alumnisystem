from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
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
