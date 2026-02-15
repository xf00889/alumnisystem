"""
Management command to migrate SSO configuration from .env to database
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import SSOConfig
import os


class Command(BaseCommand):
    help = 'Migrate SSO configuration from environment variables to database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force migration even if configurations already exist',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        self.stdout.write(self.style.SUCCESS('Starting SSO configuration migration...'))
        
        # Check for Google OAuth credentials in environment
        google_client_id = os.getenv('GOOGLE_CLIENT_ID') or os.getenv('SOCIALACCOUNT_GOOGLE_CLIENT_ID')
        google_secret = os.getenv('GOOGLE_CLIENT_SECRET') or os.getenv('SOCIALACCOUNT_GOOGLE_SECRET')
        
        # Check for Facebook OAuth credentials in environment
        facebook_app_id = os.getenv('FACEBOOK_APP_ID') or os.getenv('SOCIALACCOUNT_FACEBOOK_APP_ID')
        facebook_secret = os.getenv('FACEBOOK_APP_SECRET') or os.getenv('SOCIALACCOUNT_FACEBOOK_SECRET')
        
        created_count = 0
        skipped_count = 0
        
        # Migrate Google OAuth
        if google_client_id and google_secret:
            existing = SSOConfig.objects.filter(provider='google').exists()
            
            if not existing or force:
                if existing and force:
                    SSOConfig.objects.filter(provider='google').delete()
                    self.stdout.write(self.style.WARNING('Deleted existing Google OAuth configurations'))
                
                google_config = SSOConfig.objects.create(
                    name='Google OAuth (Migrated from .env)',
                    provider='google',
                    client_id=google_client_id,
                    secret_key=google_secret,
                    scopes='profile,email',
                    verified_email=True,
                    is_active=True,
                    enabled=True,
                    is_verified=False,
                )
                
                # Test the configuration
                success, message = google_config.test_configuration()
                
                self.stdout.write(self.style.SUCCESS(f'✓ Created Google OAuth configuration'))
                self.stdout.write(f'  Client ID: {google_client_id[:20]}...')
                self.stdout.write(f'  Test result: {message}')
                created_count += 1
            else:
                self.stdout.write(self.style.WARNING('⊘ Skipped Google OAuth (already exists, use --force to overwrite)'))
                skipped_count += 1
        else:
            self.stdout.write(self.style.WARNING('⊘ No Google OAuth credentials found in environment'))
            self.stdout.write('  Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env')
        
        # Migrate Facebook OAuth
        if facebook_app_id and facebook_secret:
            existing = SSOConfig.objects.filter(provider='facebook').exists()
            
            if not existing or force:
                if existing and force:
                    SSOConfig.objects.filter(provider='facebook').delete()
                    self.stdout.write(self.style.WARNING('Deleted existing Facebook OAuth configurations'))
                
                facebook_config = SSOConfig.objects.create(
                    name='Facebook OAuth (Migrated from .env)',
                    provider='facebook',
                    client_id=facebook_app_id,
                    secret_key=facebook_secret,
                    scopes='email,public_profile',
                    verified_email=False,
                    is_active=True,
                    enabled=True,
                    is_verified=False,
                )
                
                # Test the configuration
                success, message = facebook_config.test_configuration()
                
                self.stdout.write(self.style.SUCCESS(f'✓ Created Facebook OAuth configuration'))
                self.stdout.write(f'  App ID: {facebook_app_id[:20]}...')
                self.stdout.write(f'  Test result: {message}')
                created_count += 1
            else:
                self.stdout.write(self.style.WARNING('⊘ Skipped Facebook OAuth (already exists, use --force to overwrite)'))
                skipped_count += 1
        else:
            self.stdout.write(self.style.WARNING('⊘ No Facebook OAuth credentials found in environment'))
            self.stdout.write('  Set FACEBOOK_APP_ID and FACEBOOK_APP_SECRET in .env')
        
        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS(f'Migration complete!'))
        self.stdout.write(f'  Created: {created_count}')
        self.stdout.write(f'  Skipped: {skipped_count}')
        self.stdout.write('')
        
        if created_count > 0:
            self.stdout.write(self.style.SUCCESS('Next steps:'))
            self.stdout.write('1. Go to Admin Dashboard → SSO Configuration')
            self.stdout.write('2. Review and test your SSO configurations')
            self.stdout.write('3. Update OAuth redirect URIs in provider consoles if needed')
            self.stdout.write('4. You can now remove SSO credentials from .env file')
        
        self.stdout.write(self.style.SUCCESS('=' * 60))
