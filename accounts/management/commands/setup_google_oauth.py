from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from decouple import config
import logging

logger = logging.getLogger('accounts')


class Command(BaseCommand):
    help = 'Setup Google OAuth Social Application with credentials from environment variables'

    def handle(self, *args, **options):
        """
        Creates or updates Google Social App with credentials from environment.
        Associates with correct site based on SITE_URL.
        """
        # Validate environment variables
        client_id = config('GOOGLE_OAUTH_CLIENT_ID', default='')
        client_secret = config('GOOGLE_OAUTH_CLIENT_SECRET', default='')
        site_url = config('SITE_URL', default='http://127.0.0.1:8000')

        if not client_id or not client_secret:
            self.stdout.write(
                self.style.ERROR(
                    'Error: Missing Google OAuth credentials in environment variables.\n'
                    'Please set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET in your .env file.\n\n'
                    'Setup Instructions:\n'
                    '1. Go to Google Cloud Console: https://console.cloud.google.com/\n'
                    '2. Create or select a project\n'
                    '3. Enable Google+ API\n'
                    '4. Go to Credentials > Create Credentials > OAuth 2.0 Client ID\n'
                    '5. Set authorized redirect URI: {}/accounts/google/login/callback/\n'
                    '6. Copy Client ID and Client Secret to your .env file'
                ).format(site_url)
            )
            logger.error('Google OAuth setup failed: Missing credentials in environment variables')
            return

        # Parse site domain from SITE_URL
        # Remove protocol and trailing slash
        site_domain = site_url.replace('http://', '').replace('https://', '').rstrip('/')
        
        # Get or create Site
        try:
            site, site_created = Site.objects.get_or_create(
                domain=site_domain,
                defaults={'name': f'NORSU Alumni System ({site_domain})'}
            )
            
            if site_created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created new Site: {site.domain}')
                )
                logger.info(f'Created new Site: {site.domain}')
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'Using existing Site: {site.domain}')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating/retrieving Site: {str(e)}')
            )
            logger.error(f'Site creation/retrieval failed: {str(e)}')
            return

        # Create or update SocialApp for Google
        try:
            social_app, app_created = SocialApp.objects.get_or_create(
                provider='google',
                defaults={
                    'name': 'Google OAuth',
                    'client_id': client_id,
                    'secret': client_secret,
                }
            )
            
            if app_created:
                # Associate with site
                social_app.sites.add(site)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully created Google OAuth Social App\n'
                        f'Provider: google\n'
                        f'Client ID: {client_id[:20]}...\n'
                        f'Associated with site: {site.domain}'
                    )
                )
                logger.info(f'Created Google OAuth Social App for site: {site.domain}')
            else:
                # Update existing app
                updated = False
                if social_app.client_id != client_id:
                    social_app.client_id = client_id
                    updated = True
                if social_app.secret != client_secret:
                    social_app.secret = client_secret
                    updated = True
                
                if updated:
                    social_app.save()
                    self.stdout.write(
                        self.style.SUCCESS('Updated Google OAuth credentials')
                    )
                    logger.info('Updated Google OAuth credentials')
                
                # Ensure site association
                if site not in social_app.sites.all():
                    social_app.sites.add(site)
                    self.stdout.write(
                        self.style.SUCCESS(f'Associated Google OAuth with site: {site.domain}')
                    )
                    logger.info(f'Associated Google OAuth with site: {site.domain}')
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Google OAuth Social App already configured\n'
                            f'Provider: google\n'
                            f'Client ID: {client_id[:20]}...\n'
                            f'Associated with site: {site.domain}'
                        )
                    )
            
            # Also associate with SITE_ID=1 (default site) to ensure compatibility
            try:
                default_site = Site.objects.get(id=1)
                if default_site not in social_app.sites.all():
                    social_app.sites.add(default_site)
                    self.stdout.write(
                        self.style.SUCCESS(f'Also associated with default site: {default_site.domain}')
                    )
                    logger.info(f'Associated Google OAuth with default site: {default_site.domain}')
            except Site.DoesNotExist:
                # Site ID 1 doesn't exist, skip
                pass
            
            self.stdout.write(
                self.style.SUCCESS(
                    '\nGoogle OAuth setup complete!\n'
                    'Users can now sign in with Google at: {}/accounts/login/'
                ).format(site_url)
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating/updating Google OAuth Social App: {str(e)}')
            )
            logger.error(f'Google OAuth Social App creation/update failed: {str(e)}')
            return
