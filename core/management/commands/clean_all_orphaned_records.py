"""
Management command to clean all orphaned records (social accounts, email addresses, etc.)
"""
from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialAccount, SocialToken
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Clean all orphaned records that reference non-existent users'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Cleaning all orphaned records...'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        
        total_cleaned = 0
        
        # 1. Clean orphaned social accounts
        self.stdout.write(self.style.WARNING('1. Checking Social Accounts...'))
        orphaned_accounts = []
        for account in SocialAccount.objects.all():
            try:
                _ = account.user
            except User.DoesNotExist:
                orphaned_accounts.append(account)
        
        if orphaned_accounts:
            self.stdout.write(f'   Found {len(orphaned_accounts)} orphaned social account(s)')
            for account in orphaned_accounts:
                self.stdout.write(f'   - {account.provider} account (UID: {account.uid}, User ID: {account.user_id})')
                
                # Delete associated tokens first
                tokens_deleted = SocialToken.objects.filter(account=account).delete()[0]
                if tokens_deleted:
                    self.stdout.write(f'     Deleted {tokens_deleted} associated token(s)')
                
                # Delete the account
                account.delete()
                self.stdout.write(self.style.SUCCESS(f'     ✓ Deleted'))
                total_cleaned += 1
        else:
            self.stdout.write(self.style.SUCCESS('   ✓ No orphaned social accounts found'))
        
        self.stdout.write('')
        
        # 2. Clean orphaned email addresses
        self.stdout.write(self.style.WARNING('2. Checking Email Addresses...'))
        orphaned_emails = []
        for email_address in EmailAddress.objects.all():
            try:
                _ = email_address.user
            except User.DoesNotExist:
                orphaned_emails.append(email_address)
        
        if orphaned_emails:
            self.stdout.write(f'   Found {len(orphaned_emails)} orphaned email address(es)')
            for email_address in orphaned_emails:
                self.stdout.write(f'   - {email_address.email} (User ID: {email_address.user_id})')
                email_address.delete()
                self.stdout.write(self.style.SUCCESS(f'     ✓ Deleted'))
                total_cleaned += 1
        else:
            self.stdout.write(self.style.SUCCESS('   ✓ No orphaned email addresses found'))
        
        self.stdout.write('')
        
        # 3. Clean orphaned social tokens (without accounts)
        self.stdout.write(self.style.WARNING('3. Checking Social Tokens...'))
        orphaned_tokens = []
        for token in SocialToken.objects.all():
            try:
                _ = token.account
            except SocialAccount.DoesNotExist:
                orphaned_tokens.append(token)
        
        if orphaned_tokens:
            self.stdout.write(f'   Found {len(orphaned_tokens)} orphaned social token(s)')
            for token in orphaned_tokens:
                self.stdout.write(f'   - Token ID: {token.id}')
                token.delete()
                self.stdout.write(self.style.SUCCESS(f'     ✓ Deleted'))
                total_cleaned += 1
        else:
            self.stdout.write(self.style.SUCCESS('   ✓ No orphaned social tokens found'))
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        if total_cleaned > 0:
            self.stdout.write(self.style.SUCCESS(f'Cleanup complete! Removed {total_cleaned} orphaned record(s)'))
        else:
            self.stdout.write(self.style.SUCCESS('All clean! No orphaned records found'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
