"""
Management command to check account lockout status
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.security import AccountLockout

User = get_user_model()


class Command(BaseCommand):
    help = 'Check the lockout status of a user account'

    def add_arguments(self, parser):
        parser.add_argument(
            'identifier',
            type=str,
            help='Username or email of the account to check'
        )

    def handle(self, *args, **options):
        identifier = options['identifier']
        
        # Check if account is locked
        is_locked, remaining_minutes, failed_attempts = AccountLockout.is_account_locked(identifier)
        
        # Get current failed attempts
        current_failed_attempts = AccountLockout.get_failed_attempts(identifier)
        remaining_attempts = AccountLockout.get_remaining_attempts(identifier)
        
        self.stdout.write(self.style.HTTP_INFO(f'\nAccount Lockout Status for: {identifier}'))
        self.stdout.write('=' * 60)
        
        if is_locked:
            self.stdout.write(
                self.style.ERROR(f'Status: LOCKED')
            )
            self.stdout.write(f'Failed Attempts: {failed_attempts}')
            self.stdout.write(f'Remaining Lockout Time: {remaining_minutes} minutes')
            self.stdout.write(
                self.style.WARNING(
                    f'\nTo unlock this account, run:\n'
                    f'python manage.py unlock_account {identifier}'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Status: UNLOCKED')
            )
            self.stdout.write(f'Failed Attempts: {current_failed_attempts}/{AccountLockout.MAX_FAILED_ATTEMPTS}')
            self.stdout.write(f'Remaining Attempts: {remaining_attempts}')
            
            if current_failed_attempts > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f'\nWarning: This account has {current_failed_attempts} failed login attempt(s). '
                        f'After {AccountLockout.MAX_FAILED_ATTEMPTS} failed attempts, the account will be locked.'
                    )
                )
        
        self.stdout.write('=' * 60)
        
        # Also check by email if identifier is username
        try:
            if '@' not in identifier:
                user = User.objects.get(username=identifier)
                self.stdout.write(f'\nAlso checking by email: {user.email}')
                
                is_locked_email, remaining_minutes_email, failed_attempts_email = AccountLockout.is_account_locked(user.email)
                current_failed_email = AccountLockout.get_failed_attempts(user.email)
                
                if is_locked_email:
                    self.stdout.write(
                        self.style.ERROR(f'Email Status: LOCKED ({remaining_minutes_email} minutes remaining)')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'Email Status: UNLOCKED ({current_failed_email} failed attempts)')
                    )
        except User.DoesNotExist:
            pass
