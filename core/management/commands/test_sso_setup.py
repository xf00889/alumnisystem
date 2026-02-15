"""
Management command to test SSO setup
"""
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings
from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = 'Test SSO setup and configuration'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing SSO Setup...'))
        self.stdout.write('')
        
        # Check SITE_ID
        self.stdout.write(f'SITE_ID in settings: {settings.SITE_ID}')
        
        # Check current site
        try:
            current_site = Site.objects.get_current()
            self.stdout.write(f'Current site: {current_site.domain} (ID: {current_site.id})')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error getting current site: {str(e)}'))
            return
        
        # Check if SITE_ID matches current site
        if current_site.id != settings.SITE_ID:
            self.stdout.write(self.style.WARNING(
                f'WARNING: Current site ID ({current_site.id}) != SITE_ID ({settings.SITE_ID})'
            ))
        
        # Check SocialApps
        self.stdout.write('')
        self.stdout.write('SocialApps:')
        social_apps = SocialApp.objects.all()
        
        if not social_apps.exists():
            self.stdout.write(self.style.WARNING('  No SocialApps found!'))
        else:
            for app in social_apps:
                self.stdout.write(f'  Provider: {app.provider}')
                self.stdout.write(f'    Client ID: {app.client_id[:30]}...')
                self.stdout.write(f'    Sites: {[s.domain for s in app.sites.all()]}')
                
                # Check if current site is in the app's sites
                if current_site in app.sites.all():
                    self.stdout.write(self.style.SUCCESS('    ✓ Current site is associated'))
                else:
                    self.stdout.write(self.style.ERROR('    ✗ Current site is NOT associated'))
        
        # Check SSOConfig
        self.stdout.write('')
        self.stdout.write('SSOConfig:')
        try:
            from core.models import SSOConfig
            configs = SSOConfig.objects.filter(is_active=True, enabled=True)
            
            if not configs.exists():
                self.stdout.write(self.style.WARNING('  No active SSOConfig found!'))
            else:
                for config in configs:
                    self.stdout.write(f'  Provider: {config.provider}')
                    self.stdout.write(f'    Name: {config.name}')
                    self.stdout.write(f'    Active: {config.is_active}')
                    self.stdout.write(f'    Enabled: {config.enabled}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Error: {str(e)}'))
        
        # Test callback URL generation
        self.stdout.write('')
        self.stdout.write('Expected callback URLs:')
        self.stdout.write(f'  Google: http://{current_site.domain}/accounts/google/login/callback/')
        self.stdout.write(f'  Facebook: http://{current_site.domain}/accounts/facebook/login/callback/')
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('Setup looks good!' if social_apps.exists() else 'Setup needs attention!')
        self.stdout.write(self.style.SUCCESS('=' * 60))
