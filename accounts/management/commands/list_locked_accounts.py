"""
Management command to list all currently locked accounts
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.cache import cache
from accounts.security import AccountLockout

User = get_user_model()


class Command(BaseCommand):
    help = 'List all currently locked user accounts'

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('\nScanning for locked accounts...'))
        self.stdout.write('=' * 80)
        
        locked_accounts = []
        
        # Check all users
        for user in User.objects.all():
            # Check by username
            is_locked_username, remaining_min_username, attempts_username = AccountLockout.is_account_locked(user.username)
            
            # Check by email
            is_locked_email, remaining_min_email, attempts_email = AccountLockout.is_account_locked(user.email)
            
            if is_locked_username or is_locked_email:
                locked_accounts.append({
                    'username': user.username,
                    'email': user.email,
                    'locked_by_username': is_locked_username,
                    'locked_by_email': is_locked_email,
                    'remaining_minutes': max(remaining_min_username, remaining_min_email),
                    'failed_attempts': max(attempts_username, attempts_email)
                })
        
        if not locked_accounts:
            self.stdout.write(self.style.SUCCESS('\nNo locked accounts found.'))
        else:
            self.stdout.write(
                self.style.WARNING(f'\nFound {len(locked_accounts)} locked account(s):\n')
            )
            
            for account in locked_accounts:
                self.stdout.write(
                    self.style.ERROR(f"\nUsername: {account['username']}")
                )
                self.stdout.write(f"Email: {account['email']}")
                self.stdout.write(f"Failed Attempts: {account['failed_attempts']}")
                self.stdout.write(f"Remaining Lockout Time: {account['remaining_minutes']} minutes")
                
                if account['locked_by_username'] and account['locked_by_email']:
                    self.stdout.write("Locked By: Username and Email")
                elif account['locked_by_username']:
                    self.stdout.write("Locked By: Username only")
                else:
                    self.stdout.write("Locked By: Email only")
                
                self.stdout.write(
                    self.style.WARNING(
                        f"To unlock: python manage.py unlock_account {account['username']}"
                    )
                )
                self.stdout.write('-' * 80)
        
        self.stdout.write('=' * 80)
        self.stdout.write(
            self.style.HTTP_INFO(
                f'\nTotal users checked: {User.objects.count()}'
            )
        )
        self.stdout.write(
            self.style.HTTP_INFO(
                f'Locked accounts: {len(locked_accounts)}'
            )
        )
