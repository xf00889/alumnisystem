"""
Email utility functions for rendering HTML email templates
"""
from django.template.loader import render_to_string


def render_verification_email(user, verification_code):
    """
    Render the email verification HTML template
    
    Args:
        user: User object
        verification_code: The 6-digit verification code
    
    Returns:
        Rendered HTML content
    """
    context = {
        'user_first_name': user.first_name,
        'user_email': user.email,
        'verification_code': verification_code,
    }
    
    return render_to_string('emails/email_verification.html', context)


def render_resend_verification_email(user, verification_code):
    """
    Render the resend verification HTML template
    
    Args:
        user: User object
        verification_code: The 6-digit verification code
    
    Returns:
        Rendered HTML content
    """
    context = {
        'user_first_name': user.first_name,
        'user_email': user.email,
        'verification_code': verification_code,
    }
    
    return render_to_string('emails/resend_verification.html', context)


def render_password_reset_email(user, verification_code):
    """
    Render the password reset verification HTML template
    
    Args:
        user: User object
        verification_code: The 6-digit verification code
    
    Returns:
        Rendered HTML content
    """
    context = {
        'user_first_name': user.first_name,
        'user_email': user.email,
        'verification_code': verification_code,
    }
    
    return render_to_string('emails/password_reset_verification.html', context)
