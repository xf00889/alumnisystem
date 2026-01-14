"""
Service layer for user management operations
Provides transaction-safe methods for user creation, role assignment, and audit logging
"""
from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.template.loader import render_to_string
from django.conf import settings
from .models.user_management import UserAuditLog, UserStatusChange
from .email_utils import send_email_with_provider
from accounts.models import Profile, Mentor
import logging

User = get_user_model()
logger = logging.getLogger('accounts')


class UserManagementService:
    """Service for user management operations"""
    
    @staticmethod
    def _get_client_ip(request):
        """Extract client IP address from request"""
        if not request:
            return None
        
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @staticmethod
    @transaction.atomic
    def create_user(email, first_name, last_name, password, created_by, request=None, send_email=True):
        """
        Create a new user with profile
        
        Args:
            email: User's email address
            first_name: User's first name
            last_name: User's last name
            password: User's password
            created_by: User object of the admin creating this user
            request: HTTP request object (optional, for IP logging)
            send_email: Whether to send welcome email (default: True)
        
        Returns:
            tuple: (user, profile, success, error_message)
        """
        try:
            # Validate email format
            try:
                validate_email(email)
            except ValidationError:
                return (None, None, False, "Invalid email format")
            
            # Check email uniqueness
            if User.objects.filter(email=email).exists():
                return (None, None, False, f"User with email {email} already exists")
            
            # Validate password length
            if len(password) < 8:
                return (None, None, False, "Password must be at least 8 characters long")
            
            # Create User instance
            user = User.objects.create_user(
                username=email,  # Use email as username
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password,
                is_active=True
            )
            
            # Profile is created automatically via signal
            # Verify it exists
            try:
                profile = user.profile
            except Profile.DoesNotExist:
                # Create profile if signal failed
                profile = Profile.objects.create(user=user)
            
            # Log audit entry
            AuditLogService.log_action(
                user=user,
                action='CREATE',
                performed_by=created_by,
                details={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                },
                reason='User account created by admin',
                request=request
            )
            
            # Send welcome email
            if send_email:
                try:
                    # Get site URL from settings
                    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
                    
                    # Render HTML email template
                    html_message = render_to_string('emails/user_created.html', {
                        'user': user,
                        'password': password,
                        'site_url': site_url,
                    })
                    
                    # Plain text fallback
                    plain_message = f"""
Hello {first_name} {last_name},

Your account has been created in the NORSU Alumni System.

Email: {email}
Temporary Password: {password}

Please log in and change your password immediately.

Best regards,
NORSU Alumni System
"""
                    
                    subject = "Welcome to NORSU Alumni System"
                    send_email_with_provider(
                        subject=subject,
                        message=plain_message,
                        recipient_list=[email],
                        html_message=html_message,
                        fail_silently=True
                    )
                    logger.info(f"Welcome email sent to {email}")
                except Exception as e:
                    logger.error(f"Failed to send welcome email to {email}: {str(e)}")
                    # Don't fail the entire operation if email fails
            
            logger.info(
                f"User created successfully: {email} by {created_by.email}",
                extra={
                    'user_id': user.id,
                    'user_email': email,
                    'created_by': created_by.email,
                    'action': 'user_created'
                }
            )
            
            return (user, profile, True, None)
            
        except Exception as e:
            logger.error(
                f"Failed to create user {email}: {str(e)}",
                exc_info=True,
                extra={
                    'email': email,
                    'created_by': created_by.email if created_by else None,
                    'action': 'user_creation_failed'
                }
            )
            return (None, None, False, str(e))
    
    @staticmethod
    @transaction.atomic
    def update_user_status(user, is_active, reason, changed_by, request=None, send_email=True):
        """
        Enable or disable a user account
        
        Args:
            user: User object to update
            is_active: New active status (True/False)
            reason: Reason for status change
            changed_by: User object of the admin making the change
            request: HTTP request object (optional, for IP logging)
            send_email: Whether to send notification email (default: True)
        
        Returns:
            tuple: (success, error_message)
        """
        try:
            # Validate cannot disable self
            if user.id == changed_by.id and not is_active:
                return (False, "You cannot disable your own account")
            
            # Store old status
            old_status = user.is_active
            
            # Check if status is actually changing
            if old_status == is_active:
                return (False, f"User is already {'active' if is_active else 'inactive'}")
            
            # Update user status
            user.is_active = is_active
            user.save(update_fields=['is_active'])
            
            # Terminate sessions if disabling
            if not is_active:
                UserManagementService.terminate_user_sessions(user)
            
            # Create UserStatusChange record
            ip_address = UserManagementService._get_client_ip(request)
            UserStatusChange.objects.create(
                user=user,
                changed_by=changed_by,
                old_status=old_status,
                new_status=is_active,
                reason=reason,
                ip_address=ip_address
            )
            
            # Log audit entry
            action = 'STATUS_ENABLE' if is_active else 'STATUS_DISABLE'
            AuditLogService.log_action(
                user=user,
                action=action,
                performed_by=changed_by,
                details={
                    'old_status': old_status,
                    'new_status': is_active,
                },
                reason=reason,
                request=request
            )
            
            # Send notification email
            if send_email:
                try:
                    # Get site URL from settings
                    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
                    
                    # Render HTML email template
                    html_message = render_to_string('emails/status_changed.html', {
                        'user': user,
                        'is_active': is_active,
                        'reason': reason,
                        'site_url': site_url,
                    })
                    
                    # Plain text fallback
                    status_text = "enabled" if is_active else "disabled"
                    plain_message = f"""
Hello {user.get_full_name()},

Your account in the NORSU Alumni System has been {status_text}.

Reason: {reason}

If you have any questions, please contact the administrator.

Best regards,
NORSU Alumni System
"""
                    
                    subject = f"Your NORSU Alumni Account Has Been {status_text.title()}"
                    send_email_with_provider(
                        subject=subject,
                        message=plain_message,
                        recipient_list=[user.email],
                        html_message=html_message,
                        fail_silently=True
                    )
                    logger.info(f"Status change notification sent to {user.email}")
                except Exception as e:
                    logger.error(f"Failed to send status change email to {user.email}: {str(e)}")
                    # Don't fail the operation if email fails
            
            logger.info(
                f"User status updated: {user.email} {'enabled' if is_active else 'disabled'} by {changed_by.email}",
                extra={
                    'user_id': user.id,
                    'user_email': user.email,
                    'new_status': is_active,
                    'changed_by': changed_by.email,
                    'action': 'user_status_changed'
                }
            )
            
            return (True, None)
            
        except Exception as e:
            logger.error(
                f"Failed to update user status for {user.email}: {str(e)}",
                exc_info=True,
                extra={
                    'user_id': user.id,
                    'user_email': user.email,
                    'changed_by': changed_by.email if changed_by else None,
                    'action': 'user_status_update_failed'
                }
            )
            return (False, str(e))
    
    @staticmethod
    def terminate_user_sessions(user):
        """
        Terminate all active sessions for a user
        
        Args:
            user: User object whose sessions should be terminated
        """
        try:
            # Get all sessions
            sessions = Session.objects.filter(expire_date__gte=timezone.now())
            
            # Find sessions belonging to this user
            user_sessions = []
            for session in sessions:
                session_data = session.get_decoded()
                if session_data.get('_auth_user_id') == str(user.id):
                    user_sessions.append(session.session_key)
            
            # Delete user's sessions
            if user_sessions:
                Session.objects.filter(session_key__in=user_sessions).delete()
                logger.info(
                    f"Terminated {len(user_sessions)} session(s) for user {user.email}",
                    extra={
                        'user_id': user.id,
                        'user_email': user.email,
                        'sessions_terminated': len(user_sessions),
                        'action': 'sessions_terminated'
                    }
                )
            else:
                logger.info(f"No active sessions found for user {user.email}")
                
        except Exception as e:
            logger.error(
                f"Failed to terminate sessions for user {user.email}: {str(e)}",
                exc_info=True,
                extra={
                    'user_id': user.id,
                    'user_email': user.email,
                    'action': 'session_termination_failed'
                }
            )


class RoleAssignmentService:
    """Service for role assignment operations"""
    
    # Map role names to model fields and values
    ROLE_FIELDS = {
        'hr': ('profile.is_hr', True),
        'admin': ('is_staff', True),
        'superuser': ('is_superuser', True),
        'mentor': ('mentor_profile', 'create_or_activate'),
    }
    
    @staticmethod
    @transaction.atomic
    def assign_role(user, role_name, assigned_by, request=None, send_email=True):
        """
        Assign a role to a user
        
        Args:
            user: User object to assign role to
            role_name: Name of role ('hr', 'admin', 'superuser', 'mentor')
            assigned_by: User object of the admin assigning the role
            request: HTTP request object (optional, for IP logging)
            send_email: Whether to send notification email (default: True)
        
        Returns:
            tuple: (success, error_message)
        """
        try:
            # Validate role name
            role_name = role_name.lower()
            if role_name not in RoleAssignmentService.ROLE_FIELDS:
                return (False, f"Invalid role: {role_name}")
            
            # Check assigner permissions
            if role_name == 'superuser' and not assigned_by.is_superuser:
                return (False, "Only superusers can assign superuser role")
            
            if role_name in ['admin', 'hr'] and not (assigned_by.is_superuser or assigned_by.is_staff):
                return (False, "Insufficient permissions to assign this role")
            
            # Assign the role
            field_info = RoleAssignmentService.ROLE_FIELDS[role_name]
            
            if role_name == 'hr':
                user.profile.is_hr = True
                user.profile.save(update_fields=['is_hr'])
                
            elif role_name == 'admin':
                user.is_staff = True
                user.save(update_fields=['is_staff'])
                
            elif role_name == 'superuser':
                user.is_superuser = True
                user.is_staff = True  # Superusers should also be staff
                user.save(update_fields=['is_superuser', 'is_staff'])
                
            elif role_name == 'mentor':
                # Create or activate mentor profile
                mentor, created = Mentor.objects.get_or_create(
                    user=user,
                    defaults={
                        'expertise_areas': '',
                        'is_active': True,
                        'is_verified': True,
                        'verified_by': assigned_by,
                        'verification_date': timezone.now(),
                    }
                )
                if not created:
                    # Reactivate existing mentor profile
                    mentor.is_active = True
                    mentor.is_verified = True
                    mentor.verified_by = assigned_by
                    mentor.verification_date = timezone.now()
                    mentor.removal_reason = None
                    mentor.removed_at = None
                    mentor.removed_by = None
                    mentor.save()
            
            # Log audit entry
            AuditLogService.log_action(
                user=user,
                action='ROLE_ASSIGN',
                performed_by=assigned_by,
                details={
                    'role': role_name,
                },
                reason=f"Role '{role_name}' assigned",
                request=request
            )
            
            # Send notification email
            if send_email:
                try:
                    # Get site URL from settings
                    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
                    
                    # Render HTML email template
                    html_message = render_to_string('emails/role_assigned.html', {
                        'user': user,
                        'role_name': role_name,
                        'site_url': site_url,
                    })
                    
                    # Plain text fallback
                    plain_message = f"""
Hello {user.get_full_name()},

You have been assigned the '{role_name.title()}' role in the NORSU Alumni System.

This role grants you additional permissions and responsibilities.

Best regards,
NORSU Alumni System
"""
                    
                    subject = f"New Role Assigned: {role_name.title()}"
                    send_email_with_provider(
                        subject=subject,
                        message=plain_message,
                        recipient_list=[user.email],
                        html_message=html_message,
                        fail_silently=True
                    )
                    logger.info(f"Role assignment notification sent to {user.email}")
                except Exception as e:
                    logger.error(f"Failed to send role assignment email to {user.email}: {str(e)}")
            
            logger.info(
                f"Role '{role_name}' assigned to {user.email} by {assigned_by.email}",
                extra={
                    'user_id': user.id,
                    'user_email': user.email,
                    'role': role_name,
                    'assigned_by': assigned_by.email,
                    'action': 'role_assigned'
                }
            )
            
            return (True, None)
            
        except Exception as e:
            logger.error(
                f"Failed to assign role '{role_name}' to {user.email}: {str(e)}",
                exc_info=True,
                extra={
                    'user_id': user.id,
                    'user_email': user.email,
                    'role': role_name,
                    'assigned_by': assigned_by.email if assigned_by else None,
                    'action': 'role_assignment_failed'
                }
            )
            return (False, str(e))
    
    @staticmethod
    @transaction.atomic
    def remove_role(user, role_name, removed_by, request=None, send_email=True):
        """
        Remove a role from a user
        
        Args:
            user: User object to remove role from
            role_name: Name of role ('hr', 'admin', 'superuser', 'mentor')
            removed_by: User object of the admin removing the role
            request: HTTP request object (optional, for IP logging)
            send_email: Whether to send notification email (default: True)
        
        Returns:
            tuple: (success, error_message)
        """
        try:
            # Validate role name
            role_name = role_name.lower()
            if role_name not in RoleAssignmentService.ROLE_FIELDS:
                return (False, f"Invalid role: {role_name}")
            
            # Check remover permissions
            if role_name == 'superuser' and not removed_by.is_superuser:
                return (False, "Only superusers can remove superuser role")
            
            if role_name in ['admin', 'hr'] and not (removed_by.is_superuser or removed_by.is_staff):
                return (False, "Insufficient permissions to remove this role")
            
            # Remove the role
            if role_name == 'hr':
                user.profile.is_hr = False
                user.profile.save(update_fields=['is_hr'])
                
            elif role_name == 'admin':
                user.is_staff = False
                user.save(update_fields=['is_staff'])
                
            elif role_name == 'superuser':
                user.is_superuser = False
                user.save(update_fields=['is_superuser'])
                
            elif role_name == 'mentor':
                # Deactivate mentor profile
                try:
                    mentor = user.mentor_profile
                    mentor.is_active = False
                    mentor.removal_reason = "Role removed by admin"
                    mentor.removed_at = timezone.now()
                    mentor.removed_by = removed_by
                    mentor.save()
                except Mentor.DoesNotExist:
                    return (False, "User does not have mentor profile")
            
            # Log audit entry
            AuditLogService.log_action(
                user=user,
                action='ROLE_REMOVE',
                performed_by=removed_by,
                details={
                    'role': role_name,
                },
                reason=f"Role '{role_name}' removed",
                request=request
            )
            
            # Send notification email
            if send_email:
                try:
                    # Get site URL from settings
                    site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
                    
                    # Render HTML email template
                    html_message = render_to_string('emails/role_removed.html', {
                        'user': user,
                        'role_name': role_name,
                        'site_url': site_url,
                    })
                    
                    # Plain text fallback
                    plain_message = f"""
Hello {user.get_full_name()},

The '{role_name.title()}' role has been removed from your account in the NORSU Alumni System.

If you have any questions, please contact the administrator.

Best regards,
NORSU Alumni System
"""
                    
                    subject = f"Role Removed: {role_name.title()}"
                    send_email_with_provider(
                        subject=subject,
                        message=plain_message,
                        recipient_list=[user.email],
                        html_message=html_message,
                        fail_silently=True
                    )
                    logger.info(f"Role removal notification sent to {user.email}")
                except Exception as e:
                    logger.error(f"Failed to send role removal email to {user.email}: {str(e)}")
            
            logger.info(
                f"Role '{role_name}' removed from {user.email} by {removed_by.email}",
                extra={
                    'user_id': user.id,
                    'user_email': user.email,
                    'role': role_name,
                    'removed_by': removed_by.email,
                    'action': 'role_removed'
                }
            )
            
            return (True, None)
            
        except Exception as e:
            logger.error(
                f"Failed to remove role '{role_name}' from {user.email}: {str(e)}",
                exc_info=True,
                extra={
                    'user_id': user.id,
                    'user_email': user.email,
                    'role': role_name,
                    'removed_by': removed_by.email if removed_by else None,
                    'action': 'role_removal_failed'
                }
            )
            return (False, str(e))
    
    @staticmethod
    def get_user_roles(user):
        """
        Get list of roles assigned to a user
        
        Args:
            user: User object
        
        Returns:
            list: List of role names
        """
        roles = []
        
        # Check superuser
        if user.is_superuser:
            roles.append('superuser')
        
        # Check admin/staff
        if user.is_staff:
            roles.append('admin')
        
        # Check HR
        try:
            if user.profile.is_hr:
                roles.append('hr')
        except Profile.DoesNotExist:
            pass
        
        # Check mentor
        try:
            if user.mentor_profile.is_active:
                roles.append('mentor')
        except Mentor.DoesNotExist:
            pass
        
        return roles


class AuditLogService:
    """Service for audit log operations"""
    
    @staticmethod
    def log_action(user, action, performed_by, details=None, reason='', request=None):
        """
        Create an audit log entry
        
        Args:
            user: User object being acted upon
            action: Action type (from UserAuditLog.ACTION_CHOICES)
            performed_by: User object performing the action
            details: Dictionary of action-specific data (optional)
            reason: Reason for the action (optional)
            request: HTTP request object (optional, for IP logging)
        
        Returns:
            UserAuditLog: Created audit log entry
        """
        try:
            ip_address = UserManagementService._get_client_ip(request)
            
            audit_log = UserAuditLog.objects.create(
                user=user,
                action=action,
                performed_by=performed_by,
                details=details or {},
                reason=reason,
                ip_address=ip_address
            )
            
            logger.info(
                f"Audit log created: {action} on {user.email} by {performed_by.email if performed_by else 'System'}",
                extra={
                    'audit_log_id': audit_log.id,
                    'user_id': user.id,
                    'action': action,
                    'performed_by': performed_by.email if performed_by else 'System',
                    'ip_address': ip_address,
                }
            )
            
            return audit_log
            
        except Exception as e:
            logger.error(
                f"Failed to create audit log for {action} on {user.email}: {str(e)}",
                exc_info=True,
                extra={
                    'user_id': user.id,
                    'action': action,
                    'performed_by': performed_by.email if performed_by else None,
                }
            )
            # Don't raise exception - audit logging failure shouldn't break operations
            return None
    
    @staticmethod
    def get_user_audit_trail(user, limit=None):
        """
        Get audit trail for a specific user
        
        Args:
            user: User object
            limit: Maximum number of entries to return (optional)
        
        Returns:
            QuerySet: UserAuditLog entries for the user
        """
        queryset = UserAuditLog.objects.filter(user=user).select_related('performed_by')
        
        if limit:
            queryset = queryset[:limit]
        
        return queryset
    
    @staticmethod
    def get_recent_actions(limit=50):
        """
        Get recent audit actions across all users
        
        Args:
            limit: Maximum number of entries to return (default: 50)
        
        Returns:
            QuerySet: Recent UserAuditLog entries
        """
        return UserAuditLog.objects.select_related('user', 'performed_by')[:limit]
