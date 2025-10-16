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

logger = logging.getLogger(__name__)
User = get_user_model()


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
                from django.core.mail import EmailMultiAlternatives
                from django.conf import settings
                
                msg = EmailMultiAlternatives(
                    subject='NORSU Alumni - Email Verification Code',
                    body=f'Your verification code is: {verification_code}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[user.email]
                )
                msg.attach_alternative(html_content, "text/html")
                
                try:
                    msg.send()
                    logger.info(f"Verification email sent successfully to {user.email}")
                except Exception as email_error:
                    logger.error(f"Failed to send email to {user.email}: {str(email_error)}")
                    # Don't fail the signup if email sending fails
                    messages.warning(request, 'Account created but email could not be sent. Please contact support.')
                
                # In development mode, also log the verification code to console
                from django.conf import settings
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
                return redirect('account_login')
        else:
            # Form is not valid - redirect back to login page with error messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            return redirect('account_login')
    else:
        # GET request - redirect to login page
        return redirect('account_login')


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
                    
                    messages.success(request, 'Email verified successfully! You can now sign in.')
                    return redirect('account_login')
                    
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
                
                # Send HTML email
                html_content = render_resend_verification_email(user, verification_code)
                from django.core.mail import EmailMultiAlternatives
                from django.conf import settings
                
                msg = EmailMultiAlternatives(
                    subject='NORSU Alumni - New Verification Code',
                    body=f'Your new verification code is: {verification_code}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[email]
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()
                
                # In development mode, also log the new verification code to console
                from django.conf import settings
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
                
                # Send HTML email
                html_content = render_password_reset_email(user, verification_code)
                from django.core.mail import EmailMultiAlternatives
                from django.conf import settings
                
                msg = EmailMultiAlternatives(
                    subject='NORSU Alumni - Password Reset Code',
                    body=f'Your password reset code is: {verification_code}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[email]
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()
                
                # Log password reset request
                SecurityAuditLogger.log_password_reset_request(email, request.META.get('REMOTE_ADDR'))
                
                # Record attempt
                RateLimiter.record_attempt(email, 'password_reset_attempt')
                
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
    if request.method == 'POST':
        form = PasswordResetOTPForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
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
                
                # Send HTML email
                html_content = render_password_reset_email(user, verification_code)
                from django.core.mail import EmailMultiAlternatives
                from django.conf import settings
                
                msg = EmailMultiAlternatives(
                    subject='NORSU Alumni - New Password Reset Code',
                    body=f'Your new password reset code is: {verification_code}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[email]
                )
                msg.attach_alternative(html_content, "text/html")
                msg.send()
                
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
