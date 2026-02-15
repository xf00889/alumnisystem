"""
Management command to fix SSO SocialApp site associations
"""
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings


class Command(BaseCommand):
    help = 'Fix SSO SocialApp site associations and ensure Site is configured'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Fixing SSO site associations...'))
        
        # Check and fix Site configuration
        try:
            current_site = Site.objects.get_current()
            self.stdout.write(f'Current site: {current_site.domain} (ID: {current_site.id})')
            
            # Check if SITE_ID matches
            if hasattr(settings, 'SITE_ID'):
                if current_site.id != settings.SITE_ID:
                    self.stdout.write(self.style.WARNING(
                        f'Warning: Current site ID ({current_site.id}) does not match SITE_ID setting ({settings.SITE_ID})'
                    ))
                    
                    # Try to get the site with SITE_ID
                    try:
                        configured_site = Site.objects.get(id=settings.SITE_ID)
                        self.stdout.write(f'Configured site: {configured_site.domain} (ID: {configured_site.id})')
                        current_site = configured_site
                    except Site.DoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            f'Site with ID {settings.SITE_ID} does not exist. Using current site.'
                        ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error getting current site: {str(e)}'))
            return
        
        # Fix SocialApp associations
        try:
            from allauth.socialaccount.models import SocialApp
            from core.models import SSOConfig
            
            social_apps = SocialApp.objects.all()
            
            if not social_apps.exists():
                self.stdout.write(self.style.WARNING('No SocialApp entries found.'))
                
                # Check if there are SSOConfig entries
                sso_configs = SSOConfig.objects.filter(is_active=True, enabled=True)
                
                if sso_configs.exists():
                    self.stdout.write('Found active SSOConfig entries. Creating SocialApps...')
                    
                    for config in sso_configs:
                        social_app, created = SocialApp.objects.get_or_create(
                            provider=config.provider,
                            defaults={
                                'name': config.name,
                                'client_id': config.client_id,
                                'secret': config.secret_key,
                            }
                        )
                        
                        # Add to current site
                        social_app.sites.clear()
                        social_app.sites.add(current_site)
                        
                        action = "Created" if created else "Updated"
                        self.stdout.write(self.style.SUCCESS(
                            f'✓ {action} SocialApp for {config.provider}: {config.name}'
                        ))
                else:
                    self.stdout.write('No active SSOConfig entries found.')
                    self.stdout.write('Create SSO configurations in Admin Dashboard → SSO Configuration')
            else:
                self.stdout.write(f'Found {social_apps.count()} SocialApp(s). Fixing site associations...')
                
                for social_app in social_apps:
                    # Clear and re-add current site
                    social_app.sites.clear()
                    social_app.sites.add(current_site)
                    
                    self.stdout.write(self.style.SUCCESS(
                        f'✓ Fixed {social_app.provider}: {social_app.name} (added site {current_site.domain})'
                    ))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error fixing SocialApp associations: {str(e)}'))
            import traceback
            traceback.print_exc()
            return
        
        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Site configuration fixed!'))
        self.stdout.write(f'Site: {current_site.domain} (ID: {current_site.id})')
        self.stdout.write('')
        self.stdout.write('Next steps:')
        self.stdout.write('1. Verify OAuth redirect URIs in provider console:')
        self.stdout.write(f'   Google: http://{current_site.domain}/accounts/google/login/callback/')
        self.stdout.write(f'   Facebook: http://{current_site.domain}/accounts/facebook/login/callback/')
        self.stdout.write('2. Test SSO login')
        self.stdout.write(self.style.SUCCESS('=' * 60))
