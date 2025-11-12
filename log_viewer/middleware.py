"""
Middleware to store the current request in thread-local storage
so that signals can access it for audit logging.
"""
import threading
import logging

logger = logging.getLogger(__name__)

# Thread-local storage for the current request
_thread_locals = threading.local()


def get_current_request():
    """Get the current request from thread-local storage"""
    return getattr(_thread_locals, 'request', None)


def get_current_user():
    """Get the current user from the current request"""
    request = get_current_request()
    if request and hasattr(request, 'user'):
        return request.user if request.user.is_authenticated else None
    return None


class AuditLogMiddleware:
    """
    Middleware to store the current request in thread-local storage
    for use by audit logging signals.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Store request in thread-local storage
        _thread_locals.request = request
        
        try:
            response = self.get_response(request)
        finally:
            # Clean up thread-local storage
            if hasattr(_thread_locals, 'request'):
                delattr(_thread_locals, 'request')
        
        return response

