"""
Management command to unlock a locked user account
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.security import AccountLockout

User = get_user_model()


class Command(BaseCommand):
    help = 'Unlock a user account that has been locked due to failed login attempts'

    def add_arguments(self, parser):
        parser.add_argument(
            'identifier',
            type=str,
            help='Username or email of the account to unlock'
        )

    def handle(self, *args, **options):
        identifier = options['identifier']
        
        # Check if account is locked
        is_locked, remaining_minutes, failed_attempts = AccountLockout.is_account_locked(identifier)
        
        if not is_locked:
            self.stdout.write(
                self.style.WARNING(f'Account "{identifier}" is not currently locked.')
            )
            return
        
        # Unlock the account
        AccountLockout.unlock_account(identifier)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully unlocked account "{identifier}". '
                f'The account had {failed_attempts} failed login attempts and was locked for {remaining_minutes} more minutes.'
            )
        )
        
        # Also try to unlock by email if identifier is username
        try:
            if '@' not in identifier:
                user = User.objects.get(username=identifier)
                AccountLockout.unlock_account(user.email)
                self.stdout.write(
                    self.style.SUCCESS(f'Also unlocked by email: {user.email}')
                )
        except User.DoesNotExist:
            pass
