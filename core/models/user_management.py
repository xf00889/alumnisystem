from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class UserAuditLog(models.Model):
    """
    Audit trail for user management actions
    Tracks all administrative actions performed on user accounts
    """
    
    ACTION_CHOICES = [
        ('CREATE', _('User Created')),
        ('UPDATE', _('User Updated')),
        ('ROLE_ASSIGN', _('Role Assigned')),
        ('ROLE_REMOVE', _('Role Removed')),
        ('STATUS_ENABLE', _('User Enabled')),
        ('STATUS_DISABLE', _('User Disabled')),
        ('PASSWORD_RESET', _('Password Reset')),
        ('BULK_ACTION', _('Bulk Action')),
    ]
    
    # User being acted upon
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_management_audit_logs',
        verbose_name=_('User')
    )
    
    # Action performed
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name=_('Action')
    )
    
    # Admin who performed the action
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='user_management_actions_performed',
        verbose_name=_('Performed By')
    )
    
    # When the action occurred
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Timestamp')
    )
    
    # Action-specific data (JSON format)
    details = models.JSONField(
        default=dict,
        verbose_name=_('Details'),
        help_text=_('Stores action-specific data in JSON format')
    )
    
    # Optional reason for the action
    reason = models.TextField(
        blank=True,
        verbose_name=_('Reason')
    )
    
    # IP address of the admin performing the action
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('IP Address')
    )
    
    class Meta:
        verbose_name = _('User Audit Log')
        verbose_name_plural = _('User Audit Logs')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['performed_by', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.user.email} by {self.performed_by.email if self.performed_by else 'System'} at {self.timestamp}"


class UserStatusChange(models.Model):
    """
    Detailed tracking of user status changes
    Provides compliance and auditing for account enable/disable operations
    """
    
    # User whose status changed
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='status_changes',
        verbose_name=_('User')
    )
    
    # Admin who made the change
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='status_changes_made',
        verbose_name=_('Changed By')
    )
    
    # When the change occurred
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Timestamp')
    )
    
    # Previous status
    old_status = models.BooleanField(
        verbose_name=_('Old Status'),
        help_text=_('Previous is_active value')
    )
    
    # New status
    new_status = models.BooleanField(
        verbose_name=_('New Status'),
        help_text=_('New is_active value')
    )
    
    # Reason for the change
    reason = models.TextField(
        verbose_name=_('Reason'),
        help_text=_('Explanation for the status change')
    )
    
    # IP address of the admin making the change
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('IP Address')
    )
    
    class Meta:
        verbose_name = _('User Status Change')
        verbose_name_plural = _('User Status Changes')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['changed_by', '-timestamp']),
        ]
    
    def __str__(self):
        status_change = f"{'Enabled' if self.new_status else 'Disabled'}"
        return f"{self.user.email} {status_change} by {self.changed_by.email if self.changed_by else 'System'} at {self.timestamp}"
    
    @property
    def status_display(self):
        """Human-readable status change description"""
        if self.old_status and not self.new_status:
            return "Disabled"
        elif not self.old_status and self.new_status:
            return "Enabled"
        else:
            return "No Change"
