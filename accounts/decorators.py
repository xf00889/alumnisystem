"""
Custom decorators for authentication and email verification
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.core.paginator import Paginator
from functools import wraps

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