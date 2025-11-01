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


def custom_login_view(request):
    """Custom login view that includes reCAPTCHA context"""
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


def enhanced_signup(request):
    """Enhanced signup view with email verification - handles POST from tabbed login page"""
    if request.method == 'POST':
        form = EnhancedSignupForm(request.POST)
        
        if form.is_valid():
            try:
                # Create user
                user = form.save(request)
                
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
                    logger.error(f"Failed to send email to {user.email}: {str(email_error)}")
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
            # Form is not valid - redirect back to login page with error messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return redirect('accounts:custom_login')
    else:
        # GET request - redirect to login page
        return redirect('accounts:custom_login')


def verify_email(request):
    """Email verification view - uses existing template"""
    if request.method == 'POST':
        form = EmailVerificationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            verification_code = form.cleaned_data['verification_code']
            
            # Verify code
            is_valid, message = SecurityCodeManager.verify_code(email, verification_code, 'signup')
            
            if is_valid:
                try:
                    user = User.objects.get(email=email)
                    user.is_active = True
                    user.save()
                    
                    # Log successful verification
                    SecurityAuditLogger.log_event(
                        'email_verification_success',
                        user=user,
                        ip_address=request.META.get('REMOTE_ADDR')
                    )
                    
                    # Log the user in automatically after verification
                    login(request, user)
                    
                    messages.success(request, 'Email verified successfully! Please complete your registration.')
                    return redirect('accounts:post_registration')
                    
                except User.DoesNotExist:
                    messages.error(request, 'User not found.')
            else:
                messages.error(request, message)
    else:
        # Get email from URL parameter if available
        email = request.GET.get('email', '')
        initial_data = {'email': email} if email else {}
        form = EmailVerificationForm(initial=initial_data)
    
    # Use existing verify email template
    return render(request, 'accounts/verify_email.html', {'form': form, 'user_email': email})


def resend_verification_code(request):
    """Resend verification code"""
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            # Check rate limiting
            if RateLimiter.is_rate_limited(email, 'resend_verification'):
                return JsonResponse({
                    'success': False,
                    'error': 'Too many resend attempts. Please try again later.'
                })
            
            try:
                user = User.objects.get(email=email)
                if user.is_active:
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
                        return JsonResponse({
                            'success': False,
                            'error': 'Failed to send verification code. Please try again later.'
                        })
                except Exception as e:
                    logger.error(f"Error sending verification email to {email}: {str(e)}")
                    return JsonResponse({
                        'success': False,
                        'error': 'Failed to send verification code. Please check email configuration or try again later.'
                    })
                
                # In development mode, also log the new verification code to console
                if settings.DEBUG:
                    logger.info(f"DEVELOPMENT MODE: New verification code for {email} is: {verification_code}")
                    print(f"DEVELOPMENT MODE: New verification code for {email} is: {verification_code}")
                
                # Record attempt
                RateLimiter.record_attempt(email, 'resend_verification')
                
                return JsonResponse({
                    'success': True,
                    'message': 'New verification code sent to your email.'
                })
                
            except User.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'User not found.'
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
    """Password reset email request - uses existing template"""
    if request.method == 'POST':
        form = PasswordResetEmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            
            # Check rate limiting
            if RateLimiter.is_rate_limited(email, 'password_reset_attempt'):
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
                        messages.error(request, 'Failed to send password reset code. Please try again later.')
                        return render(request, 'accounts/password_reset_email.html', {'form': form})
                except Exception as e:
                    logger.error(f"Error sending password reset email to {email}: {str(e)}")
                    messages.error(request, 'Failed to send password reset code. Please check email configuration or try again later.')
                    return render(request, 'accounts/password_reset_email.html', {'form': form})
                
                # Log password reset request
                SecurityAuditLogger.log_password_reset_request(email, request.META.get('REMOTE_ADDR'))
                
                # Record attempt
                RateLimiter.record_attempt(email, 'password_reset_attempt')
                
                # Store email in session for OTP verification page
                request.session['password_reset_email'] = email
                
                messages.success(request, 'Verification code sent to your email.')
                return redirect('accounts:password_reset_otp')
                
            except User.DoesNotExist:
                messages.error(request, 'No account found with this email address.')
    else:
        form = PasswordResetEmailForm()
    
    # Use existing password reset email template
    return render(request, 'accounts/password_reset_email.html', {'form': form})


def password_reset_otp(request):
    """Password reset OTP verification - uses existing template"""
    # Get email from URL parameter or session
    email = request.GET.get('email') or request.session.get('password_reset_email')
    
    if not email:
        messages.error(request, 'Please enter your email address first.')
        return redirect('accounts:password_reset_email')
    
    if request.method == 'POST':
        form = PasswordResetOTPForm(request.POST)
        if form.is_valid():
            verification_code = form.cleaned_data['verification_code']
            
            # Verify code
            is_valid, message = SecurityCodeManager.verify_code(email, verification_code, 'password_reset')
            
            if is_valid:
                # Store email in session for next step
                request.session['password_reset_email'] = email
                messages.success(request, 'Email verified successfully. Please set your new password.')
                return redirect('accounts:password_reset_new_password')
            else:
                messages.error(request, message)
    else:
        # Store email in session if it came from URL parameter
        if email:
            request.session['password_reset_email'] = email
        form = PasswordResetOTPForm()
    
    # Use existing password reset OTP template
    return render(request, 'accounts/password_reset_otp.html', {'form': form, 'email': email})


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
                
                # Activate user account FIRST using update to ensure DB is immediately updated
                # This ensures the database state is correct before setting password
                User.objects.filter(email=email).update(is_active=True)
                
                # Then set and save the password
                user.set_password(form.cleaned_data['new_password1'])
                user.save(update_fields=['password'])
                
                # Refresh the user object to ensure we have the latest state
                # This prevents any caching issues during authentication
                user.refresh_from_db()
                
                # Double-check that is_active is True after refresh
                if not user.is_active:
                    # Force update if refresh didn't work
                    User.objects.filter(email=email).update(is_active=True)
                    user.refresh_from_db()
                
                # Log password reset success BEFORE clearing session
                SecurityAuditLogger.log_event(
                    'password_reset_success',
                    user=user,
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                # Clear session AFTER getting user but BEFORE redirect
                # This ensures the redirect happens with the session cleared
                if 'password_reset_email' in request.session:
                    del request.session['password_reset_email']
                
                # Save session to ensure changes are persisted
                request.session.save()
                
                messages.success(request, 'Password reset successfully! You can now sign in with your new password.')
                return redirect('account_login')
                
            except User.DoesNotExist:
                messages.error(request, 'User not found.')
                return render(request, 'accounts/password_reset_new_password.html', {'form': form, 'email': email})
    else:
        form = PasswordResetNewPasswordForm()
    
    # Use existing password reset new password template
    return render(request, 'accounts/password_reset_new_password.html', {'form': form, 'email': email})


def resend_password_reset_otp(request):
    """Resend password reset OTP"""
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            # Check rate limiting
            if RateLimiter.is_rate_limited(email, 'password_reset_attempt'):
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
                        return JsonResponse({
                            'success': False,
                            'error': 'Failed to send password reset code. Please try again later.'
                        })
                except Exception as e:
                    logger.error(f"Error sending password reset email to {email}: {str(e)}")
                    return JsonResponse({
                        'success': False,
                        'error': 'Failed to send password reset code. Please check email configuration or try again later.'
                    })
                
                # Record attempt
                RateLimiter.record_attempt(email, 'password_reset_attempt')
                
                return JsonResponse({
                    'success': True,
                    'message': 'New verification code sent to your email.'
                })
                
            except User.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'User not found.'
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


@csrf_exempt
@require_POST
def csp_report_view(request):
    """
    Handle CSP violation reports for monitoring and debugging
    """
    try:
        # Parse the CSP report
        report_data = json.loads(request.body.decode('utf-8'))
        csp = report_data.get('csp-report') or report_data.get('csp_report') or {}

        # Extract commonly useful fields for a concise, single-line log
        violated = csp.get('violated-directive')
        blocked = csp.get('blocked-uri')
        src = csp.get('source-file')
        line = csp.get('line-number')
        doc = csp.get('document-uri')
        ref = csp.get('referrer')
        ua = request.META.get('HTTP_USER_AGENT', '-')

        # Deduplicate noisy repeats for 5 minutes (in-memory cache)
        signature = f"{violated}|{blocked}|{src}"
        cache_key = f"csp_sig:{signature}"
        if cache.get(cache_key):
            # Already seen recently; keep noise down
            return JsonResponse({'status': 'deduplicated'}, status=200)
        cache.set(cache_key, True, timeout=300)

        # Log a clean, single-line summary first
        logger.warning(
            "CSP violation: directive=%s blocked=%s source=%s line=%s doc=%s ref=%s ua=%s",
            violated, blocked, src, line, doc, ref, ua
        )

        # Also log full raw JSON at DEBUG level for deep dives
        logger.debug("CSP raw: %s", json.dumps(report_data, separators=(',', ':'), ensure_ascii=False))

        return JsonResponse({'status': 'received'}, status=200)
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in CSP report")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Error processing CSP report: {str(e)}")
        return JsonResponse({'error': 'Internal server error'}, status=500)
