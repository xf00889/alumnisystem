"""
Management command to clean orphaned social accounts
"""
from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialAccount, SocialToken
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Clean orphaned social accounts that reference non-existent users'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Cleaning orphaned social accounts...'))
        
        # Find social accounts with non-existent users
        orphaned_accounts = []
        for account in SocialAccount.objects.all():
            try:
                # Try to access the user
                _ = account.user
            except User.DoesNotExist:
                orphaned_accounts.append(account)
        
        if not orphaned_accounts:
            self.stdout.write(self.style.SUCCESS('No orphaned social accounts found!'))
            return
        
        self.stdout.write(f'Found {len(orphaned_accounts)} orphaned social account(s):')
        
        for account in orphaned_accounts:
            self.stdout.write(f'  - {account.provider} account (UID: {account.uid}, User ID: {account.user_id})')
            
            # Delete associated tokens first
            tokens_deleted = SocialToken.objects.filter(account=account).delete()[0]
            if tokens_deleted:
                self.stdout.write(f'    Deleted {tokens_deleted} associated token(s)')
            
            # Delete the account
            account.delete()
            self.stdout.write(self.style.SUCCESS(f'    ✓ Deleted orphaned {account.provider} account'))
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS(f'Cleanup complete! Removed {len(orphaned_accounts)} orphaned account(s)'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
