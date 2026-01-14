"""
Permission mixins for user management and admin access control.

These mixins provide reusable permission checks for class-based views,
ensuring proper authorization and logging of access attempts.
"""

from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
import logging

logger = logging.getLogger('core')


class SuperuserRequiredMixin(UserPassesTestMixin):
    """
    Mixin that requires superuser access for the view.
    
    This mixin restricts access to users with is_superuser=True.
    Unauthorized access attempts are logged for security auditing.
    
    Usage:
        class MyView(SuperuserRequiredMixin, View):
            ...
    """
    
    def test_func(self):
        """Check if the user is a superuser"""
        user = self.request.user
        
        if not user.is_authenticated:
            return False
        
        is_superuser = user.is_superuser
        
        if not is_superuser:
            logger.warning(
                f"Unauthorized superuser access attempt by user {user.id} ({user.email})",
                extra={
                    'user_id': user.id,
                    'user_email': user.email,
                    'username': user.username,
                    'view': self.__class__.__name__,
                    'path': self.request.path,
                    'ip_address': self.request.META.get('REMOTE_ADDR'),
                    'action': 'unauthorized_superuser_access'
                }
            )
        
        return is_superuser
    
    def handle_no_permission(self):
        """
        Handle unauthorized access attempts.
        
        Redirects to admin dashboard with an error message.
        Logs the unauthorized access for security auditing.
        """
        if self.request.user.is_authenticated:
            logger.warning(
                f"Permission denied for user {self.request.user.id} accessing {self.__class__.__name__}",
                extra={
                    'user_id': self.request.user.id,
                    'user_email': self.request.user.email,
                    'view': self.__class__.__name__,
                    'path': self.request.path,
                    'ip_address': self.request.META.get('REMOTE_ADDR'),
                    'action': 'permission_denied'
                }
            )
            messages.error(
                self.request,
                'You do not have permission to access this page. Superuser privileges are required.'
            )
            return redirect(reverse('core:admin_dashboard'))
        
        # If not authenticated, use default behavior (redirect to login)
        return super().handle_no_permission()


class StaffRequiredMixin(UserPassesTestMixin):
    """
    Mixin that requires staff or superuser access for the view.
    
    This mixin allows access to users with is_staff=True or is_superuser=True.
    Typically used for read-only admin views where staff can view but not modify.
    Unauthorized access attempts are logged for security auditing.
    
    Usage:
        class MyView(StaffRequiredMixin, View):
            ...
    """
    
    def test_func(self):
        """Check if the user is staff or superuser"""
        user = self.request.user
        
        if not user.is_authenticated:
            return False
        
        has_access = user.is_staff or user.is_superuser
        
        if not has_access:
            logger.warning(
                f"Unauthorized staff access attempt by user {user.id} ({user.email})",
                extra={
                    'user_id': user.id,
                    'user_email': user.email,
                    'username': user.username,
                    'view': self.__class__.__name__,
                    'path': self.request.path,
                    'ip_address': self.request.META.get('REMOTE_ADDR'),
                    'action': 'unauthorized_staff_access'
                }
            )
        
        return has_access
    
    def handle_no_permission(self):
        """
        Handle unauthorized access attempts.
        
        Redirects to admin dashboard with an error message.
        Logs the unauthorized access for security auditing.
        """
        if self.request.user.is_authenticated:
            logger.warning(
                f"Permission denied for user {self.request.user.id} accessing {self.__class__.__name__}",
                extra={
                    'user_id': self.request.user.id,
                    'user_email': self.request.user.email,
                    'view': self.__class__.__name__,
                    'path': self.request.path,
                    'ip_address': self.request.META.get('REMOTE_ADDR'),
                    'action': 'permission_denied'
                }
            )
            messages.error(
                self.request,
                'You do not have permission to access this page. Staff privileges are required.'
            )
            return redirect(reverse('core:admin_dashboard'))
        
        # If not authenticated, use default behavior (redirect to login)
        return super().handle_no_permission()
