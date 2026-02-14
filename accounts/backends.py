"""
Custom authentication backends with brute-force protection
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q
from .security import AccountLockout, SecurityAuditLogger
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class CustomModelBackend(ModelBackend):
    """
    Custom authentication backend with account lockout protection.
    Prevents brute-force attacks by locking accounts after failed attempts.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user with email/username and password.
        Includes account lockout protection against brute-force attacks.
        """
        if username is None:
            username = kwargs.get('email') or kwargs.get(User.USERNAME_FIELD)
        
        if username is None or password is None:
            return None
        
        # Get IP address for logging
        ip_address = request.META.get('REMOTE_ADDR') if request else 'unknown'
        
        # Check if account is locked BEFORE attempting authentication
        is_locked, remaining_minutes, failed_attempts = AccountLockout.is_account_locked(username)
        if is_locked:
            logger.warning(
                f"Login attempt for locked account: {username} from IP {ip_address} "
                f"(locked for {remaining_minutes} more minutes after {failed_attempts} failed attempts)"
            )
            SecurityAuditLogger.log_event(
                'login_attempt_locked_account',
                ip_address=ip_address,
                details={
                    'username': username,
                    'remaining_minutes': remaining_minutes,
                    'failed_attempts': failed_attempts
                }
            )
            # Return None to indicate authentication failure
            # The view will handle displaying the lockout message
            return None
        
        try:
            # Always get user directly from database (bypassing any cache)
            # Check by email first, then username
            if '@' in username:
                user = User.objects.get(email=username)
            else:
                user = User.objects.get(
                    Q(username=username) | Q(email=username)
                )
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user
            User().set_password(password)
            
            # Record failed attempt even for non-existent users to prevent enumeration
            AccountLockout.record_failed_login(username)
            
            logger.warning(f"Login attempt for non-existent user: {username} from IP {ip_address}")
            SecurityAuditLogger.log_failed_login(username, ip_address, "User does not exist")
            
            return None
        
        # Refresh user from database to ensure we have the latest state
        # This is critical for users who just reset their password
        user.refresh_from_db()
        
        # Check password
        if user.check_password(password) and self.user_can_authenticate(user):
            # Successful login - reset failed attempts
            AccountLockout.reset_failed_attempts(username)
            AccountLockout.reset_failed_attempts(user.email)  # Also reset by email
            
            logger.info(f"Successful login: {user.username} ({user.email}) from IP {ip_address}")
            SecurityAuditLogger.log_successful_login(user, ip_address)
            
            return user
        else:
            # Failed login - record attempt
            locked, lockout_duration = AccountLockout.record_failed_login(username)
            AccountLockout.record_failed_login(user.email)  # Also track by email
            
            remaining_attempts = AccountLockout.get_remaining_attempts(username)
            
            if locked:
                logger.warning(
                    f"Account locked after failed login: {username} from IP {ip_address} "
                    f"(locked for {lockout_duration} minutes)"
                )
                SecurityAuditLogger.log_event(
                    'account_locked_failed_attempts',
                    user=user,
                    ip_address=ip_address,
                    details={
                        'lockout_duration_minutes': lockout_duration,
                        'failed_attempts': AccountLockout.MAX_FAILED_ATTEMPTS
                    }
                )
            else:
                logger.warning(
                    f"Failed login attempt: {username} from IP {ip_address} "
                    f"({remaining_attempts} attempts remaining)"
                )
                SecurityAuditLogger.log_failed_login(
                    username, 
                    ip_address, 
                    f"Invalid credentials ({remaining_attempts} attempts remaining)"
                )
            
            return None
    
    def user_can_authenticate(self, user):
        """
        Check if the user can authenticate.
        Always check the latest is_active status from the database.
        If user is inactive but has a password, auto-activate them.
        """
        # Refresh user from database to ensure we have the latest state
        user.refresh_from_db()
        
        # Check if user is active
        is_active = getattr(user, 'is_active', None)
        
        # If user is not active but has a usable password, they likely reset password
        # Auto-activate them to allow login
        if not is_active and user.has_usable_password():
            # User has a password but is inactive - likely reset password
            # Activate them automatically
            user.is_active = True
            user.save(update_fields=['is_active'])
            user.refresh_from_db()
            return True
        
        return is_active is True

