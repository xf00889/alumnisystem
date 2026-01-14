"""
Custom decorators for authentication and email verification
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.core.paginator import Paginator
from functools import wraps
import logging

logger = logging.getLogger('accounts')

def email_verified_required(view_func):
    """
    Decorator that requires the user to be authenticated and have verified their email.
    Redirects unverified users to the email verification page.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please log in to access this page.')
            return redirect('account_login')
        
        if not request.user.is_active:
            messages.warning(request, 'Please verify your email address to access this page.')
            return redirect('accounts:verify_email')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def post_registration_required(view_func):
    """
    Decorator that requires the user to have completed post-registration.
    Redirects users who haven't completed post-registration to the post-registration page.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Please log in to access this page.')
            return redirect('account_login')
        
        if not request.user.is_active:
            messages.warning(request, 'Please verify your email address to access this page.')
            return redirect('accounts:verify_email')
        
        # Check if user has completed post-registration
        try:
            profile = request.user.profile
            if not profile.first_name or not profile.last_name:
                messages.info(request, 'Please complete your profile to access this page.')
                return redirect('accounts:post_registration')
        except:
            messages.info(request, 'Please complete your profile to access this page.')
            return redirect('accounts:post_registration')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def paginate(per_page=10):
    """
    Decorator to add pagination to a view
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Get the result from the view
            result = view_func(request, *args, **kwargs)
            
            # If it's a render response, add pagination
            if hasattr(result, 'context_data'):
                context = result.context_data
                if 'applications' in context:
                    paginator = Paginator(context['applications'], per_page)
                    page_number = request.GET.get('page')
                    page_obj = paginator.get_page(page_number)
                    context['page_obj'] = page_obj
                    context['applications'] = page_obj.object_list
            
            return result
        return wrapper
    return decorator


def hr_required(function=None, redirect_field_name='next', login_url=None):
    """
    Decorator for views that checks that the user is logged in and has HR status.
    Logs unauthorized access attempts.
    Superusers always have access regardless of HR status.
    """
    def check_hr(user):
        if not user.is_authenticated:
            return False
        
        # Superusers always have access
        if user.is_superuser:
            return True
        
        # Check if user has HR status
        try:
            has_hr = user.profile.is_hr
            if not has_hr:
                logger.warning(
                    f"Unauthorized HR access attempt by user {user.id} ({user.email})",
                    extra={'user_id': user.id, 'user_email': user.email}
                )
            return has_hr
        except Exception as e:
            logger.error(
                f"Error checking HR status for user {user.id}: {str(e)}",
                extra={'user_id': user.id},
                exc_info=True
            )
            return False
    
    actual_decorator = user_passes_test(
        check_hr,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    
    if function:
        return actual_decorator(function)
    return actual_decorator