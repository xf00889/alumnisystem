"""
Rate limiting decorators for messaging and other sensitive operations
"""
from functools import wraps
from django.core.cache import cache
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import redirect


def rate_limit_messages(max_messages=10, time_window=60):
    """
    Rate limit message sending
    
    Args:
        max_messages: Maximum number of messages allowed
        time_window: Time window in seconds
        
    Usage:
        @rate_limit_messages(max_messages=10, time_window=60)
        def send_message(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return view_func(request, *args, **kwargs)
            
            # Create cache key for this user
            cache_key = f'message_rate_limit_{request.user.id}'
            
            # Get current count
            current_count = cache.get(cache_key, 0)
            
            # Check if limit exceeded
            if current_count >= max_messages:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'error': f'Rate limit exceeded. Please wait before sending more messages.'
                    }, status=429)
                else:
                    messages.error(
                        request,
                        f'You are sending messages too quickly. Please wait a moment.'
                    )
                    return redirect(request.META.get('HTTP_REFERER', '/'))
            
            # Increment counter
            cache.set(cache_key, current_count + 1, time_window)
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator
