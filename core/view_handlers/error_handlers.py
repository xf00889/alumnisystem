from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.conf import settings
import logging
import traceback

logger = logging.getLogger(__name__)

def handler500(request):
    """Custom 500 error handler"""
    logger.error(f"500 error on {request.path}")
    logger.error(f"User: {getattr(request, 'user', 'Anonymous')}")
    logger.error(f"Method: {request.method}")
    
    # Log POST data for debugging (excluding sensitive fields)
    if request.method == 'POST':
        post_data = dict(request.POST)
        # Remove sensitive fields
        sensitive_fields = ['password', 'password1', 'password2', 'csrfmiddlewaretoken']
        for field in sensitive_fields:
            if field in post_data:
                post_data[field] = '[REDACTED]'
        logger.error(f"POST data: {post_data}")
    
    # Log session info
    logger.error(f"Session key: {getattr(request, 'session', {}).get('_session_key', 'None')}")
    
    # Log headers (excluding sensitive ones)
    headers = dict(request.META)
    sensitive_headers = ['HTTP_AUTHORIZATION', 'HTTP_COOKIE']
    for header in sensitive_headers:
        if header in headers:
            headers[header] = '[REDACTED]'
    logger.error(f"Request headers: {headers}")
    
    # Log the actual exception if available
    import sys
    exc_info = sys.exc_info()
    if exc_info[0] is not None:
        logger.error(f"Exception type: {exc_info[0].__name__}")
        logger.error(f"Exception message: {str(exc_info[1])}")
        logger.error(f"Traceback:", exc_info=True)
    
    if settings.DEBUG:
        # In debug mode, show detailed error
        return HttpResponse(
            f"<h1>Server Error (500)</h1>"
            f"<p>Path: {request.path}</p>"
            f"<p>Method: {request.method}</p>"
            f"<p>Check logs for details</p>",
            status=500
        )
    else:
        # In production, show generic error
        try:
            return render(request, '500.html', status=500)
        except:
            return HttpResponse(
                "<h1>Server Error</h1><p>Something went wrong. Please try again later.</p>",
                status=500
            )

def health_check_view(request):
    """Simple health check endpoint"""
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'debug': settings.DEBUG
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=500)