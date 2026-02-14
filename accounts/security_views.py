"""
Security views for authentication and verification
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.urls import reverse_lazy
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from django_ratelimit.decorators import ratelimit
import json
import logging

from .forms import (
    EnhancedSignupForm, 
    EmailVerificationForm, 
    PasswordResetEmailForm,
    PasswordResetOTPForm,
    PasswordResetNewPasswordForm
)
from .security import SecurityCodeManager, RateLimiter, SecurityAuditLogger
from .email_utils import render_verification_email, render_resend_verification_email, render_password_reset_email
from core.recaptcha_utils import get_recaptcha_public_key, is_recaptcha_enabled

logger = logging.getLogger(__name__)
User = get_user_model()


@ratelimit(key='ip', rate='10/m', method='ALL', block=True)
def custom_login_view(request):
    """Custom login view with reCAPTCHA context, rate limiting, and account lockout protection"""
    from .security import AccountLockout
    
    # Check if request was rate limited by IP
    if getattr(request, 'limited', False):
        logger.warning(f"Rate limit exceeded for login from IP: {request.META.get('REMOTE_ADDR')}")
        messages.error(request, "Too many login attempts from your IP address. Please wait a moment and try again.")
        return redirect('account_login')
    
    # Check for account lockout on POST (login attempt)
    if request.method == 'POST':
        username = request.POST.get('login', '')  # allauth uses 'login' field
        
        if username:
            # Check if account is locked
            is_locked, remaining_minutes, failed_attempts = AccountLockout.is_account_locked(username)
            
            if is_locked:
                logger.warning(
                    f"Login attempt for locked account: {username} from IP {request.META.get('REMOTE_ADDR')} "
                    f"({remaining_minutes} minutes remaining)"
                )
                
                # Display lockout message
                if remaining_minutes > 0:
                    messages.error(
                        request,
                        f"Your account has been temporarily locked due to multiple failed login attempts. "
                        f"Please try again in {remaining_minutes} minute{'s' if remaining_minutes != 1 else ''}. "
                        f"If you forgot your password, use the 'Forgot Password' link."
                    )
                else:
                    messages.error(
                        request,
                        "Your account has been temporarily locked due to multiple failed login attempts. "
                        "Please try again in a few moments."
                    )
                
                # Redirect back to login page
                return redirect('account_login')
            
            # Check remaining attempts and show warning if low
            remaining_attempts = AccountLockout.get_remaining_attempts(username)
            if 0 < remaining_attempts <= 2:
                messages.warning(
                    request,
                    f"Warning: You have {remaining_attempts} login attempt{'s' if remaining_attempts != 1 else ''} "
                    f"remaining before your account is temporarily locked."
                )
    
    from allauth.account.views import LoginView
    
    # Get reCAPTCHA context
    context = {
        'recaptcha_enabled': is_recaptcha_enabled(),
        'recaptcha_public_key': get_recaptcha_public_key(),
    }
    
    # Use Allauth's LoginView but with custom context
    view = LoginView.as_view()
    response = view(request)
    
    # If it's a render response, add our context
    if hasattr(response, 'context_data'):
        response.context_data.update(context)
    
    return response


@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def enhanced_signup(request):
    """Enhanced signup view with email verification and rate limiting - handles POST from tabbed login page"""
    if request.method == 'POST':
        # Check if request was rate limited
        if getattr(request, 'limited', False):
            logger.warning(f"Rate limit exceeded for signup from IP: {request.META.get('REMOTE_ADDR')}")
            messages.error(request, "Too many signup attempts. Please wait a moment and try again.")
            return redirect('account_login')
        
        # Log the incoming request for debugging
        logger.info(f"Signup attempt from IP: {request.META.get('REMOTE_ADDR')}")
        
        form = EnhancedSignupForm(request.POST)
        
        if form.is_valid():
            try:
                # Create user
                user = form.save(request)
                logger.info(f"User created successfully: {user.email}")
                
                # Send verification email
                verification_code = SecurityCodeManager.generate_code()
                SecurityCodeManager.store_code(user.email, verification_code, 'signup')
                
                # Send HTML email
                html_content = render_verification_email(user, verification_code)
                from core.email_utils import send_email_with_provider
                from django.conf import settings
                
                # Send verification email using Render-compatible system
                plain_message = f"""
Hello!

Thank you for signing up for the NORSU Alumni Network. To complete your registration, please use the following verification code:

Verification Code: {verification_code}

This code will expire in 15 minutes.

If you didn't request this code, please ignore this email.

Best regards,
NORSU Alumni Network Team
                """
                
                try:
                    success = send_email_with_provider(
                        subject='NORSU Alumni - Email Verification Code',
                        message=plain_message,
                        recipient_list=[user.email],
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        html_message=html_content,
                        fail_silently=False
                    )
                    
                    if success:
                        logger.info(f"Verification email sent successfully to {user.email}")
                    else:
                        logger.error(f"Failed to send email to {user.email}")
                        messages.warning(request, 'Account created but email could not be sent. Please contact support.')
                        
                except Exception as email_error:
                    logger.error(f"Failed to send email to {user.email}: {str(email_error)}", exc_info=True)
                    # Don't fail the signup if email sending fails
                    messages.warning(request, 'Account created but email could not be sent. Please contact support.')
                
                # In development mode, also log the verification code to console
                if settings.DEBUG:
                    logger.info(f"DEVELOPMENT MODE: Verification code for {user.email} is: {verification_code}")
                    print(f"DEVELOPMENT MODE: Verification code for {user.email} is: {verification_code}")
                
                # Log account creation
                SecurityAuditLogger.log_account_creation(user.email, request.META.get('REMOTE_ADDR'))
                
                messages.success(request, 'Account created successfully! Please check your email for verification code.')
                # Pass the email to the verification page
                return redirect(f'/accounts/verify-email/?email={user.email}')
                
            except Exception as e:
                logger.error(f"Signup error: {str(e)}", exc_info=True)
                messages.error(request, f'An error occurred during signup: {str(e)}')
                # Redirect back to login page with error message
                return redirect('accounts:custom_login')
        else:
            # Form is not valid - log the errors for debugging
            logger.warning(f"Signup form validation failed. Errors: {form.errors.as_json()}")
            for field, errors in form.errors.items():
                for error in errors:
                    logger.warning(f"Form error - {field}: {error}")
                    messages.error(request, f"{field}: {error}")
            return redirect('accounts:custom_login')
    else:
        # GET request - redirect to login page
        return redirect('accounts:custom_login')


def verify_email(request):
    """Email verification view with comprehensive security logging"""
    if request.method == 'POST':
        form = EmailVerificationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            verification_code = form.cleaned_data['verification_code']
            
            # Log verification attempt for security audit
            SecurityAuditLogger.log_event(
                'email_verification_attempt',
                ip_address=request.META.get('REMOTE_ADDR'),
                details={'email': email}
            )
            
            # Verify code
            is_valid, message = SecurityCodeManager.verify_code(email, verification_code, 'signup')
            
            if is_valid:
                try:
                    user = User.objects.get(email=email)
                    user.is_active = True
                    user.save()
                    
                    # Log successful verification
                    logger.info(f"Email verification successful for {user.email} (IP: {request.META.get('REMOTE_ADDR')})")
                    SecurityAuditLogger.log_event(
                        'email_verification_success',
                        user=user,
                        ip_address=request.META.get('REMOTE_ADDR')
                    )
                    
                    # Auto-login the user with secure session
                    login(request, user, backend='accounts.backends.CustomModelBackend')
                    
                    # Ensure session security settings
                    request.session.set_expiry(settings.SESSION_COOKIE_AGE if hasattr(settings, 'SESSION_COOKIE_AGE') else 1209600)  # 2 weeks default
                    
                    # Log auto-login event
                    logger.info(f"User auto-logged in after email verification: {user.email} (IP: {request.META.get('REMOTE_ADDR')})")
                    SecurityAuditLogger.log_event(
                        'auto_login_after_verification',
                        user=user,
                        ip_address=request.META.get('REMOTE_ADDR')
                    )
                    
                    # Check if user has completed post-registration
                    try:
                        profile = user.profile
                        if not profile.has_completed_registration:
                            # User hasn't completed post-registration, redirect there
                            # Store success message in session for display with delay
                            request.session['verification_success'] = True
                            request.session['verification_message'] = 'Email verified successfully! Completing your profile...'
                            return redirect('accounts:post_registration')
                        else:
                            # User has already completed post-registration, go to home
                            messages.success(request, 'Email verified successfully! Welcome back.')
                            return redirect('core:home')
                    except Exception as e:
                        logger.error(f"Error checking post-registration status: {str(e)} (IP: {request.META.get('REMOTE_ADDR')})")
                        # Fallback to post-registration if there's an error
                        request.session['verification_success'] = True
                        request.session['verification_message'] = 'Email verified successfully! Completing your profile...'
                        return redirect('accounts:post_registration')
                    
                except User.DoesNotExist:
                    # Email enumeration prevention: Generic error message
                    logger.warning(f"Email verification attempted for non-existent user (IP: {request.META.get('REMOTE_ADDR')})")
                    SecurityAuditLogger.log_event(
                        'email_verification_user_not_found',
                        ip_address=request.META.get('REMOTE_ADDR'),
                        details={'attempted_email': email}
                    )
                    messages.error(request, 'Unable to verify email. Please try again.')
            else:
                # Log failed verification attempt
                logger.warning(f"Email verification failed for {email}: {message} (IP: {request.META.get('REMOTE_ADDR')})")
                SecurityAuditLogger.log_event(
                    'email_verification_failed',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    details={'email': email, 'reason': message}
                )
                messages.error(request, message)
    else:
        # Get email from URL parameter if available
        email = request.GET.get('email', '')
        initial_data = {'email': email} if email else {}
        form = EmailVerificationForm(initial=initial_data)
    
    # Use existing verify email template
    return render(request, 'accounts/verify_email.html', {'form': form, 'user_email': email})


def resend_verification_code(request):
    """Resend verification code with enhanced security"""
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            # Log verification attempt for security audit
            SecurityAuditLogger.log_event(
                'resend_verification_attempt',
                ip_address=request.META.get('REMOTE_ADDR'),
                details={'email': email}
            )
            
            # Check rate limiting (3 attempts per 15 minutes as per requirements)
            if RateLimiter.is_rate_limited(email, 'resend_verification', max_attempts=3, window_minutes=15):
                logger.warning(f"Rate limit exceeded for resend verification: {email} (IP: {request.META.get('REMOTE_ADDR')})")
                SecurityAuditLogger.log_event(
                    'resend_verification_rate_limited',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    details={'email': email}
                )
                return JsonResponse({
                    'success': False,
                    'error': 'Too many resend attempts. Please try again later.'
                })
            
            try:
                user = User.objects.get(email=email)
                if user.is_active:
                    SecurityAuditLogger.log_event(
                        'resend_verification_already_active',
                        user=user,
                        ip_address=request.META.get('REMOTE_ADDR')
                    )
                    return JsonResponse({
                        'success': False,
                        'error': 'Email is already verified.'
                    })
                
                # Generate new code
                verification_code = SecurityCodeManager.generate_code()
                SecurityCodeManager.store_code(email, verification_code, 'signup')
                
                # Send HTML email using Render-compatible system
                html_content = render_resend_verification_email(user, verification_code)
                from core.email_utils import send_email_with_provider
                from django.conf import settings
                
                plain_message = f"""
Hello!

You have requested a new verification code for your NORSU Alumni Network account. Please use the following code to complete your registration:

New Verification Code: {verification_code}

This code will expire in 15 minutes.

If you didn't request this code, please ignore this email.

Best regards,
NORSU Alumni Network Team
                """
                
                try:
                    success = send_email_with_provider(
                        subject='NORSU Alumni - New Verification Code',
                        message=plain_message,
                        recipient_list=[email],
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        html_message=html_content,
                        fail_silently=False
                    )
                    
                    if not success:
                        logger.error(f"Failed to send verification email to {email} (IP: {request.META.get('REMOTE_ADDR')})")
                        SecurityAuditLogger.log_event(
                            'resend_verification_email_failed',
                            user=user,
                            ip_address=request.META.get('REMOTE_ADDR')
                        )
                        return JsonResponse({
                            'success': False,
                            'error': 'Failed to send verification code. Please try again later.'
                        })
                except Exception as e:
                    logger.error(f"Error sending verification email to {email}: {str(e)} (IP: {request.META.get('REMOTE_ADDR')})")
                    SecurityAuditLogger.log_event(
                        'resend_verification_email_exception',
                        user=user,
                        ip_address=request.META.get('REMOTE_ADDR'),
                        details={'error': str(e)}
                    )
                    return JsonResponse({
                        'success': False,
                        'error': 'Failed to send verification code. Please check email configuration or try again later.'
                    })
                
                # In development mode, also log the new verification code to console
                if settings.DEBUG:
                    logger.info(f"DEVELOPMENT MODE: New verification code for {email} is: {verification_code}")
                    print(f"DEVELOPMENT MODE: New verification code for {email} is: {verification_code}")
                
                # Record attempt (3 attempts per 15 minutes)
                RateLimiter.record_attempt(email, 'resend_verification', max_attempts=3, window_minutes=15)
                
                # Log successful resend
                SecurityAuditLogger.log_event(
                    'resend_verification_success',
                    user=user,
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'New verification code sent to your email.'
                })
                
            except User.DoesNotExist:
                # Email enumeration prevention: Use generic error message
                logger.warning(f"Resend verification attempted for non-existent email (IP: {request.META.get('REMOTE_ADDR')})")
                SecurityAuditLogger.log_event(
                    'resend_verification_user_not_found',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    details={'attempted_email': email}
                )
                # Still record attempt to prevent enumeration attacks
                RateLimiter.record_attempt(email, 'resend_verification', max_attempts=3, window_minutes=15)
                return JsonResponse({
                    'success': False,
                    'error': 'Unable to send verification code. Please try again later.'
                })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})


def check_resend_countdown(request):
    """Check if user can resend verification code"""
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            can_resend = not RateLimiter.is_rate_limited(email, 'resend_verification')
            return JsonResponse({
                'success': True,
                'can_resend': can_resend
            })
    
    return JsonResponse({'success': False})


def custom_signup_redirect(request):
    """Custom signup redirect after allauth signup"""
    return redirect('accounts:verify_email')


def password_reset_email(request):
    """Password reset email request with enhanced security"""
    if request.method == 'POST':
        form = PasswordResetEmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            
            # Log password reset attempt for security audit
            SecurityAuditLogger.log_event(
                'password_reset_email_attempt',
                ip_address=request.META.get('REMOTE_ADDR'),
                details={'email': email}
            )
            
            # Check rate limiting (3 attempts per 15 minutes as per requirements)
            if RateLimiter.is_rate_limited(email, 'password_reset_attempt', max_attempts=3, window_minutes=15):
                logger.warning(f"Rate limit exceeded for password reset: {email} (IP: {request.META.get('REMOTE_ADDR')})")
                SecurityAuditLogger.log_event(
                    'password_reset_rate_limited',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    details={'email': email}
                )
                messages.error(request, 'Too many password reset attempts. Please try again later.')
                return render(request, 'accounts/password_reset_email.html', {'form': form})
            
            try:
                user = User.objects.get(email=email)
                
                # Generate verification code
                verification_code = SecurityCodeManager.generate_code()
                SecurityCodeManager.store_code(email, verification_code, 'password_reset')
                
                # Send HTML email using Render-compatible system
                html_content = render_password_reset_email(user, verification_code)
                from core.email_utils import send_email_with_provider
                from django.conf import settings
                
                plain_message = f"""
Hello!

You have requested to reset your password for the NORSU Alumni Network. Please use the following code to reset your password:

Password Reset Code: {verification_code}

This code will expire in 15 minutes.

If you didn't request this password reset, please ignore this email and your password will remain unchanged.

Best regards,
NORSU Alumni Network Team
                """
                
                try:
                    success = send_email_with_provider(
                        subject='NORSU Alumni - Password Reset Code',
                        message=plain_message,
                        recipient_list=[email],
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        html_message=html_content,
                        fail_silently=False
                    )
                    
                    if not success:
                        logger.error(f"Failed to send password reset email to {email} (IP: {request.META.get('REMOTE_ADDR')})")
                        SecurityAuditLogger.log_event(
                            'password_reset_email_failed',
                            user=user,
                            ip_address=request.META.get('REMOTE_ADDR')
                        )
                        messages.error(request, 'Failed to send password reset code. Please try again later.')
                        return render(request, 'accounts/password_reset_email.html', {'form': form})
                except Exception as e:
                    logger.error(f"Error sending password reset email to {email}: {str(e)} (IP: {request.META.get('REMOTE_ADDR')})")
                    SecurityAuditLogger.log_event(
                        'password_reset_email_exception',
                        user=user,
                        ip_address=request.META.get('REMOTE_ADDR'),
                        details={'error': str(e)}
                    )
                    messages.error(request, 'Failed to send password reset code. Please check email configuration or try again later.')
                    return render(request, 'accounts/password_reset_email.html', {'form': form})
                
                # Log password reset request
                logger.info(f"Password reset code sent to {email} (IP: {request.META.get('REMOTE_ADDR')})")
                SecurityAuditLogger.log_password_reset_request(email, request.META.get('REMOTE_ADDR'))
                
                # Record attempt (3 attempts per 15 minutes)
                RateLimiter.record_attempt(email, 'password_reset_attempt', max_attempts=3, window_minutes=15)
                
                messages.success(request, 'Verification code sent to your email.')
                return redirect('accounts:password_reset_otp')
                
            except User.DoesNotExist:
                # Email enumeration prevention: Generic error message
                logger.warning(f"Password reset attempted for non-existent email (IP: {request.META.get('REMOTE_ADDR')})")
                SecurityAuditLogger.log_event(
                    'password_reset_user_not_found',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    details={'attempted_email': email}
                )
                # Still record attempt to prevent enumeration attacks
                RateLimiter.record_attempt(email, 'password_reset_attempt', max_attempts=3, window_minutes=15)
                messages.error(request, 'If an account exists with this email, you will receive a password reset code.')
    else:
        form = PasswordResetEmailForm()
    
    # Use existing password reset email template
    return render(request, 'accounts/password_reset_email.html', {'form': form})


def password_reset_otp(request):
    """Password reset OTP verification with security logging"""
    if request.method == 'POST':
        form = PasswordResetOTPForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            verification_code = form.cleaned_data['verification_code']
            
            # Log OTP verification attempt
            SecurityAuditLogger.log_event(
                'password_reset_otp_attempt',
                ip_address=request.META.get('REMOTE_ADDR'),
                details={'email': email}
            )
            
            # Verify code
            is_valid, message = SecurityCodeManager.verify_code(email, verification_code, 'password_reset')
            
            if is_valid:
                # Log successful OTP verification
                logger.info(f"Password reset OTP verified for {email} (IP: {request.META.get('REMOTE_ADDR')})")
                SecurityAuditLogger.log_event(
                    'password_reset_otp_success',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    details={'email': email}
                )
                
                # Store email in session for next step with secure session settings
                request.session['password_reset_email'] = email
                request.session.set_expiry(900)  # 15 minutes for password reset session
                
                messages.success(request, 'Email verified successfully. Please set your new password.')
                return redirect('accounts:password_reset_new_password')
            else:
                # Log failed OTP verification
                logger.warning(f"Password reset OTP failed for {email}: {message} (IP: {request.META.get('REMOTE_ADDR')})")
                SecurityAuditLogger.log_event(
                    'password_reset_otp_failed',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    details={'email': email, 'reason': message}
                )
                messages.error(request, message)
    else:
        form = PasswordResetOTPForm()
    
    # Use existing password reset OTP template
    return render(request, 'accounts/password_reset_otp.html', {'form': form})


def password_reset_new_password(request):
    """Set new password after OTP verification - uses existing template"""
    email = request.session.get('password_reset_email')
    if not email:
        messages.error(request, 'Session expired. Please start the password reset process again.')
        return redirect('accounts:password_reset_email')
    
    if request.method == 'POST':
        form = PasswordResetNewPasswordForm(request.POST)
        if form.is_valid():
            try:
                user = User.objects.get(email=email)
                user.set_password(form.cleaned_data['new_password1'])
                user.save()
                
                # Clear session
                del request.session['password_reset_email']
                
                # Log password reset success
                SecurityAuditLogger.log_event(
                    'password_reset_success',
                    user=user,
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                messages.success(request, 'Password reset successfully! You can now sign in with your new password.')
                return redirect('account_login')
                
            except User.DoesNotExist:
                messages.error(request, 'User not found.')
    else:
        form = PasswordResetNewPasswordForm()
    
    # Use existing password reset new password template
    return render(request, 'accounts/password_reset_new_password.html', {'form': form})


def resend_password_reset_otp(request):
    """Resend password reset OTP with enhanced security"""
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            # Log resend attempt
            SecurityAuditLogger.log_event(
                'password_reset_resend_attempt',
                ip_address=request.META.get('REMOTE_ADDR'),
                details={'email': email}
            )
            
            # Check rate limiting (3 attempts per 15 minutes)
            if RateLimiter.is_rate_limited(email, 'password_reset_attempt', max_attempts=3, window_minutes=15):
                logger.warning(f"Rate limit exceeded for password reset resend: {email} (IP: {request.META.get('REMOTE_ADDR')})")
                SecurityAuditLogger.log_event(
                    'password_reset_resend_rate_limited',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    details={'email': email}
                )
                return JsonResponse({
                    'success': False,
                    'error': 'Too many password reset attempts. Please try again later.'
                })
            
            try:
                user = User.objects.get(email=email)
                
                # Generate new code
                verification_code = SecurityCodeManager.generate_code()
                SecurityCodeManager.store_code(email, verification_code, 'password_reset')
                
                # Send HTML email using Render-compatible system
                html_content = render_password_reset_email(user, verification_code)
                from core.email_utils import send_email_with_provider
                from django.conf import settings
                
                plain_message = f"""
Hello!

You have requested a new password reset code for your NORSU Alumni Network account. Please use the following code to reset your password:

New Password Reset Code: {verification_code}

This code will expire in 15 minutes.

If you didn't request this password reset, please ignore this email and your password will remain unchanged.

Best regards,
NORSU Alumni Network Team
                """
                
                try:
                    success = send_email_with_provider(
                        subject='NORSU Alumni - New Password Reset Code',
                        message=plain_message,
                        recipient_list=[email],
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        html_message=html_content,
                        fail_silently=False
                    )
                    
                    if not success:
                        logger.error(f"Failed to resend password reset email to {email} (IP: {request.META.get('REMOTE_ADDR')})")
                        SecurityAuditLogger.log_event(
                            'password_reset_resend_email_failed',
                            user=user,
                            ip_address=request.META.get('REMOTE_ADDR')
                        )
                        return JsonResponse({
                            'success': False,
                            'error': 'Failed to send password reset code. Please try again later.'
                        })
                except Exception as e:
                    logger.error(f"Error resending password reset email to {email}: {str(e)} (IP: {request.META.get('REMOTE_ADDR')})")
                    SecurityAuditLogger.log_event(
                        'password_reset_resend_email_exception',
                        user=user,
                        ip_address=request.META.get('REMOTE_ADDR'),
                        details={'error': str(e)}
                    )
                    return JsonResponse({
                        'success': False,
                        'error': 'Failed to send password reset code. Please check email configuration or try again later.'
                    })
                
                # Record attempt (3 attempts per 15 minutes)
                RateLimiter.record_attempt(email, 'password_reset_attempt', max_attempts=3, window_minutes=15)
                
                # Log successful resend
                logger.info(f"Password reset code resent to {email} (IP: {request.META.get('REMOTE_ADDR')})")
                SecurityAuditLogger.log_event(
                    'password_reset_resend_success',
                    user=user,
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'New verification code sent to your email.'
                })
                
            except User.DoesNotExist:
                # Email enumeration prevention: Generic error message
                logger.warning(f"Password reset resend attempted for non-existent email (IP: {request.META.get('REMOTE_ADDR')})")
                SecurityAuditLogger.log_event(
                    'password_reset_resend_user_not_found',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    details={'attempted_email': email}
                )
                # Still record attempt to prevent enumeration attacks
                RateLimiter.record_attempt(email, 'password_reset_attempt', max_attempts=3, window_minutes=15)
                return JsonResponse({
                    'success': False,
                    'error': 'Unable to send password reset code. Please try again later.'
                })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})


def check_password_reset_countdown(request):
    """Check if user can resend password reset OTP"""
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            can_resend = not RateLimiter.is_rate_limited(email, 'password_reset_attempt')
            return JsonResponse({
                'success': True,
                'can_resend': can_resend
            })
    
    return JsonResponse({'success': False})


def resend_verification_from_inactive(request):
    """Resend verification email from inactive account page with comprehensive error handling"""
    if request.method == 'POST':
        # Try to get email from session first (set during login attempt)
        email = request.session.get('inactive_account_email')
        
        # If not in session, try to get from POST
        if not email:
            email = request.POST.get('email')
        
        # Error Case 1: User Not Found (generic message for security)
        if not email:
            logger.warning(f"Resend verification attempted without email from IP: {request.META.get('REMOTE_ADDR')}")
            return JsonResponse({
                'success': False,
                'message': 'Unable to send verification email. Please try logging in again.'
            })
        
        # Error Case 2: Rate Limiting Exceeded (with countdown message)
        if RateLimiter.is_rate_limited(email, 'resend_verification_inactive'):
            # Get remaining time for countdown
            remaining_seconds = RateLimiter.get_remaining_time(email, 'resend_verification_inactive')
            logger.info(f"Rate limit exceeded for resend verification: {email} (IP: {request.META.get('REMOTE_ADDR')})")
            return JsonResponse({
                'success': False,
                'message': f'Too many resend attempts. Please wait {remaining_seconds} seconds before trying again.',
                'countdown': remaining_seconds
            })
        
        try:
            user = User.objects.get(email=email)
            
            # Error Case 4: Already Active Account (redirect to login)
            if user.is_active:
                logger.info(f"Resend verification attempted for already active account: {email}")
                SecurityAuditLogger.log_event(
                    'resend_verification_already_active',
                    user=user,
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                return JsonResponse({
                    'success': False,
                    'message': 'Your account is already verified. Please log in.',
                    'redirect_url': '/accounts/login/'
                })
            
            # Generate new verification code
            verification_code = SecurityCodeManager.generate_code()
            SecurityCodeManager.store_code(email, verification_code, 'signup')
            
            # Send HTML email using Render-compatible system
            html_content = render_resend_verification_email(user, verification_code)
            from core.email_utils import send_email_with_provider
            from django.conf import settings
            
            plain_message = f"""
Hello!

You have requested a new verification code for your NORSU Alumni Network account. Please use the following code to complete your registration:

New Verification Code: {verification_code}

This code will expire in 15 minutes.

If you didn't request this code, please ignore this email.

Best regards,
NORSU Alumni Network Team
            """
            
            # Error Case 3: Email Sending Failure (with retry suggestion)
            try:
                success = send_email_with_provider(
                    subject='NORSU Alumni - New Verification Code',
                    message=plain_message,
                    recipient_list=[email],
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    html_message=html_content,
                    fail_silently=False
                )
                
                if not success:
                    logger.error(f"Email service failed to send verification email to {email} (IP: {request.META.get('REMOTE_ADDR')})")
                    SecurityAuditLogger.log_event(
                        'verification_email_send_failed',
                        user=user,
                        ip_address=request.META.get('REMOTE_ADDR'),
                        details={'reason': 'Email service returned False'}
                    )
                    return JsonResponse({
                        'success': False,
                        'message': 'Failed to send verification email. Please try again in a few moments or contact support if the problem persists.'
                    })
            except Exception as e:
                logger.error(f"Exception sending verification email to {email}: {str(e)} (IP: {request.META.get('REMOTE_ADDR')})", exc_info=True)
                SecurityAuditLogger.log_event(
                    'verification_email_send_exception',
                    user=user,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    details={'error': str(e)}
                )
                return JsonResponse({
                    'success': False,
                    'message': 'Failed to send verification email due to a technical issue. Please try again later or contact support.'
                })
            
            # In development mode, also log the verification code to console
            if settings.DEBUG:
                logger.info(f"DEVELOPMENT MODE: New verification code for {email} is: {verification_code}")
                print(f"DEVELOPMENT MODE: New verification code for {email} is: {verification_code}")
            
            # Record attempt for rate limiting (60-second cooldown as per requirements)
            RateLimiter.record_attempt(email, 'resend_verification_inactive', max_attempts=3, window_minutes=1)
            
            # Log successful resend event for admin investigation
            logger.info(f"Verification email resent successfully to {email} from inactive page (IP: {request.META.get('REMOTE_ADDR')})")
            SecurityAuditLogger.log_event(
                'verification_resend_from_inactive_success',
                user=user,
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Verification email sent successfully! Please check your inbox.',
                'redirect_url': f'/accounts/verify-email/?email={email}'
            })
            
        except User.DoesNotExist:
            # Error Case 1: User Not Found (generic message - don't reveal if email exists)
            logger.warning(f"Resend verification attempted for non-existent email from IP: {request.META.get('REMOTE_ADDR')}")
            SecurityAuditLogger.log_event(
                'resend_verification_user_not_found',
                ip_address=request.META.get('REMOTE_ADDR'),
                details={'attempted_email': email}
            )
            return JsonResponse({
                'success': False,
                'message': 'Unable to send verification email. Please try logging in again.'
            })
        except Exception as e:
            # Catch-all for unexpected errors
            logger.error(f"Unexpected error in resend_verification_from_inactive for {email}: {str(e)} (IP: {request.META.get('REMOTE_ADDR')})", exc_info=True)
            SecurityAuditLogger.log_event(
                'resend_verification_unexpected_error',
                ip_address=request.META.get('REMOTE_ADDR'),
                details={'error': str(e), 'email': email}
            )
            return JsonResponse({
                'success': False,
                'message': 'An unexpected error occurred. Please try again later or contact support.'
            })
    
    # GET request - redirect to login
    return redirect('account_login')


def send_verification_code(request):
    """Send verification code API endpoint"""
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        purpose = data.get('purpose', 'signup')
        
        if email:
            # Check rate limiting
            if RateLimiter.is_rate_limited(email, f'{purpose}_attempt'):
                return JsonResponse({
                    'success': False,
                    'error': 'Too many attempts. Please try again later.'
                })
            
            # Generate and send code
            code = SecurityCodeManager.generate_code()
            SecurityCodeManager.store_code(email, code, purpose)
            
            success = SecurityCodeManager.send_verification_email(email, code, purpose)
            
            if success:
                RateLimiter.record_attempt(email, f'{purpose}_attempt')
                return JsonResponse({'success': True})
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Failed to send verification code.'
                })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})


def verify_code(request):
    """Verify code API endpoint"""
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        code = data.get('code')
        purpose = data.get('purpose', 'signup')
        
        if email and code:
            is_valid, message = SecurityCodeManager.verify_code(email, code, purpose)
            return JsonResponse({
                'success': is_valid,
                'message': message
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})


def enhanced_password_reset(request):
    """Enhanced password reset view"""
    return redirect('accounts:password_reset_email')


def change_password(request):
    """Change password view for logged-in users"""
    if not request.user.is_authenticated:
        return redirect('account_login')
    
    if request.method == 'POST':
        form = PasswordResetNewPasswordForm(request.POST)
        if form.is_valid():
            request.user.set_password(form.cleaned_data['new_password1'])
            request.user.save()
            
            # Log password change
            SecurityAuditLogger.log_event(
                'password_change_success',
                user=request.user,
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, 'Password changed successfully!')
            return redirect('accounts:profile_detail')
    else:
        form = PasswordResetNewPasswordForm()
    
    return render(request, 'accounts/change_password.html', {'form': form})


def check_email_availability(request):
    """Check if email is available for signup"""
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        
        if email:
            exists = User.objects.filter(email=email).exists()
            return JsonResponse({
                'available': not exists,
                'email': email,
                'message': 'Email is available' if not exists else 'Email is already registered'
            })
    
    return JsonResponse({'available': False})


@method_decorator(login_required, name='dispatch')
class SecurityDashboardView(TemplateView):
    """Security dashboard for users"""
    template_name = 'accounts/security_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context
