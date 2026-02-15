"""
Management command to check SSO and authentication database health
"""
from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialAccount, SocialToken, SocialApp
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site

User = get_user_model()


class Command(BaseCommand):
    help = 'Check SSO and authentication database health'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('SSO Health Check'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        
        issues_found = 0
        
        # 1. Check Users
        self.stdout.write(self.style.WARNING('1. Users'))
        user_count = User.objects.count()
        self.stdout.write(f'   Total users: {user_count}')
        if user_count > 0:
            self.stdout.write(f'   User IDs: {list(User.objects.values_list("id", flat=True))}')
        self.stdout.write('')
        
        # 2. Check Social Accounts
        self.stdout.write(self.style.WARNING('2. Social Accounts'))
        social_accounts = SocialAccount.objects.all()
        self.stdout.write(f'   Total: {social_accounts.count()}')
        
        orphaned_accounts = []
        for account in social_accounts:
            try:
                _ = account.user
                self.stdout.write(f'   ✓ {account.provider} - User ID: {account.user_id} ({account.user.email})')
            except User.DoesNotExist:
                orphaned_accounts.append(account)
                self.stdout.write(self.style.ERROR(f'   ✗ ORPHANED: {account.provider} - User ID: {account.user_id} (user does not exist)'))
                issues_found += 1
        
        if not social_accounts.exists():
            self.stdout.write('   (none)')
        self.stdout.write('')
        
        # 3. Check Email Addresses
        self.stdout.write(self.style.WARNING('3. Email Addresses'))
        email_addresses = EmailAddress.objects.all()
        self.stdout.write(f'   Total: {email_addresses.count()}')
        
        orphaned_emails = []
        for email in email_addresses:
            try:
                _ = email.user
                verified = '✓ verified' if email.verified else '✗ not verified'
                primary = '(primary)' if email.primary else ''
                self.stdout.write(f'   ✓ {email.email} - User ID: {email.user_id} {verified} {primary}')
            except User.DoesNotExist:
                orphaned_emails.append(email)
                self.stdout.write(self.style.ERROR(f'   ✗ ORPHANED: {email.email} - User ID: {email.user_id} (user does not exist)'))
                issues_found += 1
        
        if not email_addresses.exists():
            self.stdout.write('   (none)')
        self.stdout.write('')
        
        # 4. Check Social Tokens
        self.stdout.write(self.style.WARNING('4. Social Tokens'))
        social_tokens = SocialToken.objects.all()
        self.stdout.write(f'   Total: {social_tokens.count()}')
        
        orphaned_tokens = []
        for token in social_tokens:
            try:
                _ = token.account
                self.stdout.write(f'   ✓ Token ID: {token.id} - Account: {token.account.provider}')
            except SocialAccount.DoesNotExist:
                orphaned_tokens.append(token)
                self.stdout.write(self.style.ERROR(f'   ✗ ORPHANED: Token ID: {token.id} (account does not exist)'))
                issues_found += 1
        
        if not social_tokens.exists():
            self.stdout.write('   (none)')
        self.stdout.write('')
        
        # 5. Check Social Apps
        self.stdout.write(self.style.WARNING('5. Social Apps (django-allauth)'))
        social_apps = SocialApp.objects.all()
        self.stdout.write(f'   Total: {social_apps.count()}')
        
        for app in social_apps:
            sites = app.sites.all()
            site_names = ', '.join([s.domain for s in sites])
            self.stdout.write(f'   ✓ {app.provider}: {app.name}')
            self.stdout.write(f'     Client ID: {app.client_id[:20]}...')
            self.stdout.write(f'     Sites: {site_names if site_names else "NONE (needs fix!)"}')
            if not sites.exists():
                issues_found += 1
        
        if not social_apps.exists():
            self.stdout.write('   (none)')
        self.stdout.write('')
        
        # 6. Check SSO Config
        self.stdout.write(self.style.WARNING('6. SSO Configuration'))
        try:
            from core.models import SSOConfig
            sso_configs = SSOConfig.objects.all()
            self.stdout.write(f'   Total: {sso_configs.count()}')
            
            for config in sso_configs:
                status = '✓ active' if config.is_active else '✗ inactive'
                enabled = 'enabled' if config.enabled else 'DISABLED'
                verified = '✓ verified' if config.is_verified else '✗ not verified'
                self.stdout.write(f'   {status} {config.provider}: {config.name} ({enabled}, {verified})')
                self.stdout.write(f'     Login count: {config.login_count}')
            
            if not sso_configs.exists():
                self.stdout.write('   (none)')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   Error checking SSO config: {str(e)}'))
        
        self.stdout.write('')
        
        # 7. Check Site Configuration
        self.stdout.write(self.style.WARNING('7. Site Configuration'))
        try:
            current_site = Site.objects.get_current()
            self.stdout.write(f'   Current site: {current_site.domain} (ID: {current_site.id})')
            self.stdout.write(f'   Site name: {current_site.name}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   Error: {str(e)}'))
            issues_found += 1
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        # Summary
        if issues_found > 0:
            self.stdout.write(self.style.ERROR(f'⚠ Found {issues_found} issue(s)'))
            self.stdout.write('')
            self.stdout.write('Run this command to fix orphaned records:')
            self.stdout.write(self.style.WARNING('  python manage.py clean_all_orphaned_records'))
        else:
            self.stdout.write(self.style.SUCCESS('✓ All checks passed! Database is healthy'))
        
        self.stdout.write(self.style.SUCCESS('=' * 60))
