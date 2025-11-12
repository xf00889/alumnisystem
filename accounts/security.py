"""
Enhanced security features for authentication
"""
import secrets
import string
from datetime import datetime, timedelta
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.crypto import get_random_string
from .email_utils import render_verification_email, render_resend_verification_email, render_password_reset_email
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class SecurityCodeManager:
    """Manages security codes for email verification and password reset"""
    
    @staticmethod
    def generate_code(length=6):
        """Generate a secure numeric code"""
        return ''.join(secrets.choice(string.digits) for _ in range(length))
    
    @staticmethod
    def generate_token(length=32):
        """Generate a secure alphanumeric token"""
        return get_random_string(length=length)
    
    @staticmethod
    def store_code(email, code, purpose, expiry_minutes=15):
        """Store security code in cache with expiry"""
        cache_key = f"security_code_{purpose}_{email}"
        cache_data = {
            'code': code,
            'created_at': timezone.now().isoformat(),
            'attempts': 0,
            'max_attempts': 3
        }
        cache.set(cache_key, cache_data, timeout=expiry_minutes * 60)
        return cache_key
    
    @staticmethod
    def verify_code(email, code, purpose):
        """Verify security code"""
        cache_key = f"security_code_{purpose}_{email}"
        cache_data = cache.get(cache_key)
        
        if not cache_data:
            return False, "Code has expired or doesn't exist"
        
        # Check attempts
        if cache_data['attempts'] >= cache_data['max_attempts']:
            cache.delete(cache_key)
            return False, "Too many failed attempts. Please request a new code."
        
        # Verify code
        if cache_data['code'] == code:
            cache.delete(cache_key)
            return True, "Code verified successfully"
        else:
            # Increment attempts
            cache_data['attempts'] += 1
            cache.set(cache_key, cache_data, timeout=900)  # 15 minutes
            remaining_attempts = cache_data['max_attempts'] - cache_data['attempts']
            return False, f"Invalid code. {remaining_attempts} attempts remaining."
    
    @staticmethod
    def send_verification_email(email, code, purpose):
        """Send verification email with security code"""
        try:
            # Get user object for email template context
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                # For signup, user might not exist yet, create a temporary user object
                if purpose == 'signup':
                    user = type('User', (), {'first_name': '', 'email': email})()
                else:
                    logger.error(f"User not found for email {email}")
                    return False
            
            # Create email with HTML template
            if purpose == 'signup':
                subject = 'NORSU Alumni - Email Verification Code'
                html_content = render_verification_email(user, code)
                plain_message = f"""
Hello!

Thank you for signing up for the NORSU Alumni Network. To complete your registration, please use the following verification code:

Verification Code: {code}

This code will expire in 15 minutes.

If you didn't request this code, please ignore this email.

Best regards,
NORSU Alumni Network Team
                """
            elif purpose == 'password_reset':
                subject = 'NORSU Alumni - Password Reset Code'
                html_content = render_password_reset_email(user, code)
                plain_message = f"""
Hello!

You have requested to reset your password for the NORSU Alumni Network. Please use the following code to reset your password:

Reset Code: {code}

This code will expire in 15 minutes.

If you didn't request this password reset, please ignore this email and your password will remain unchanged.

Best regards,
NORSU Alumni Network Team
                """
            else:
                return False
            
            # Send HTML email with plain text fallback using Render-compatible system
            from core.email_utils import send_email_with_provider
            
            success = send_email_with_provider(
                subject=subject,
                message=plain_message,
                recipient_list=[email],
                from_email=settings.DEFAULT_FROM_EMAIL,
                html_message=html_content,
                fail_silently=False
            )
            
            if success:
                logger.info(f"Security code sent to {email} for {purpose}")
                return True
            else:
                logger.error(f"Failed to send security code to {email}")
                return False
        except Exception as e:
            logger.error(f"Failed to send security code to {email}: {str(e)}")
            return False

class RateLimiter:
    """Rate limiting for authentication attempts"""
    
    @staticmethod
    def is_rate_limited(identifier, action, max_attempts=5, window_minutes=15):
        """Check if identifier is rate limited for specific action"""
        cache_key = f"rate_limit_{action}_{identifier}"
        attempts = cache.get(cache_key, 0)
        return attempts >= max_attempts
    
    @staticmethod
    def record_attempt(identifier, action, max_attempts=5, window_minutes=15):
        """Record an attempt for rate limiting"""
        cache_key = f"rate_limit_{action}_{identifier}"
        attempts = cache.get(cache_key, 0) + 1
        cache.set(cache_key, attempts, timeout=window_minutes * 60)
        
        # Log rate limit attempt for security audit
        logger.info(f"Rate limit attempt recorded: {action} for {identifier} (attempt {attempts}/{max_attempts})")
        
        return attempts
    
    @staticmethod
    def get_remaining_attempts(identifier, action, max_attempts=5):
        """Get remaining attempts before rate limit"""
        cache_key = f"rate_limit_{action}_{identifier}"
        attempts = cache.get(cache_key, 0)
        return max(0, max_attempts - attempts)
    
    @staticmethod
    def reset_rate_limit(identifier, action):
        """Reset rate limit for identifier"""
        cache_key = f"rate_limit_{action}_{identifier}"
        cache.delete(cache_key)
        logger.info(f"Rate limit reset: {action} for {identifier}")
    
    @staticmethod
    def get_remaining_time(identifier, action):
        """Get remaining time in seconds before rate limit expires"""
        cache_key = f"rate_limit_{action}_{identifier}"
        # Get the TTL (time to live) of the cache key
        ttl = cache.ttl(cache_key)
        return max(0, ttl) if ttl is not None else 0

class PasswordValidator:
    """Enhanced password validation"""
    
    @staticmethod
    def validate_password_strength(password):
        """Validate password strength"""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long.")
        
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter.")
        
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter.")
        
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number.")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character.")
        
        # Check for common passwords
        common_passwords = [
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey'
        ]
        
        if password.lower() in common_passwords:
            errors.append("Password is too common. Please choose a stronger password.")
        
        return errors
    
    @staticmethod
    def check_password_history(user, new_password):
        """Check if password was used recently (last 5 passwords)"""
        # This would require implementing password history tracking
        # For now, we'll return True (password is acceptable)
        return True

class SecurityAuditLogger:
    """Log security events for audit purposes"""
    
    @staticmethod
    def log_event(event_type, user=None, ip_address=None, details=None):
        """Log security event"""
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'event_type': event_type,
            'user_id': user.id if user else None,
            'username': user.username if user else None,
            'ip_address': ip_address,
            'details': details or {}
        }
        
        logger.info(f"Security Event: {event_type}", extra=log_data)
    
    @staticmethod
    def log_failed_login(email, ip_address, reason="Invalid credentials"):
        """Log failed login attempt"""
        SecurityAuditLogger.log_event(
            'failed_login',
            ip_address=ip_address,
            details={'email': email, 'reason': reason}
        )
    
    @staticmethod
    def log_successful_login(user, ip_address):
        """Log successful login"""
        SecurityAuditLogger.log_event(
            'successful_login',
            user=user,
            ip_address=ip_address
        )
    
    @staticmethod
    def log_password_reset_request(email, ip_address):
        """Log password reset request"""
        SecurityAuditLogger.log_event(
            'password_reset_request',
            ip_address=ip_address,
            details={'email': email}
        )
    
    @staticmethod
    def log_account_creation(email, ip_address):
        """Log account creation"""
        SecurityAuditLogger.log_event(
            'account_creation',
            ip_address=ip_address,
            details={'email': email}
        )
