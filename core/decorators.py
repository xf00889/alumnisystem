"""
Custom decorators for access control and permissions
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required


def is_admin_user(user):
    """
    Helper function to check if user has admin privileges.
    Returns True if user is superuser, staff, or alumni coordinator.
    """
    if not user.is_authenticated:
        return False
    
    is_coordinator = hasattr(user, 'profile') and user.profile.is_alumni_coordinator
    return user.is_superuser or user.is_staff or is_coordinator


def superuser_required(view_func):
    """
    Decorator that requires the user to be a superuser.
    Alumni Coordinators are NOT allowed.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(
                request,
                'You do not have permission to access this page. Superuser privileges are required.'
            )
            return redirect(reverse('core:admin_dashboard'))
        return view_func(request, *args, **kwargs)
    return wrapper


def staff_or_coordinator_required(view_func):
    """
    Decorator that requires the user to be staff, superuser, or alumni coordinator.
    This is for general admin pages that coordinators can access with full CRUD permissions.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        is_coordinator = hasattr(request.user, 'profile') and request.user.profile.is_alumni_coordinator
        has_access = request.user.is_staff or request.user.is_superuser or is_coordinator
        
        if not has_access:
            messages.error(
                request,
                'You do not have permission to access this page. Admin privileges are required.'
            )
            return redirect(reverse('core:home'))
        return view_func(request, *args, **kwargs)
    return wrapper


def system_config_required(view_func):
    """
    Decorator that requires superuser access for system configuration pages.
    Alumni Coordinators are explicitly NOT allowed to access these pages.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Only superusers can access system configuration
        if not request.user.is_superuser:
            is_coordinator = hasattr(request.user, 'profile') and request.user.profile.is_alumni_coordinator
            
            if is_coordinator:
                messages.error(
                    request,
                    'Alumni Coordinators do not have access to system configuration. Please contact a system administrator.'
                )
            else:
                messages.error(
                    request,
                    'You do not have permission to access system configuration. Superuser privileges are required.'
                )
            return redirect(reverse('core:admin_dashboard'))
        return view_func(request, *args, **kwargs)
    return wrapper
