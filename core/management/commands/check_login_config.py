"""
Management command to check SSO and reCAPTCHA configuration for login page
"""
from django.core.management.base import BaseCommand
from django.core.cache import cache
from core.models.sso_config import SSOConfig
from core.models.recaptcha_config import ReCaptchaConfig
from core.sso_utils import get_enabled_sso_providers, clear_sso_cache
from core.recaptcha_utils import is_recaptcha_enabled, get_recaptcha_public_key, clear_recaptcha_cache


class Command(BaseCommand):
    help = 'Check SSO and reCAPTCHA configuration for login page display'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Clear SSO and reCAPTCHA caches before checking',
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix common configuration issues',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('LOGIN PAGE CONFIGURATION CHECK'))
        self.stdout.write(self.style.SUCCESS('=' * 80))

        # Clear caches if requested
        if options['clear_cache']:
            self.stdout.write('\nClearing caches...')
            clear_sso_cache()
            clear_recaptcha_cache()
            self.stdout.write(self.style.SUCCESS('✓ Caches cleared'))

        # Check SSO Configuration
        self.stdout.write('\n1. SSO CONFIGURATION')
        self.stdout.write('-' * 80)
        
        sso_configs = SSOConfig.objects.all()
        self.stdout.write(f'Total SSO configs: {sso_configs.count()}')
        
        active_sso = SSOConfig.objects.filter(is_active=True, enabled=True)
        
        if not active_sso.exists():
            self.stdout.write(self.style.ERROR('✗ No active and enabled SSO configurations'))
            
            if options['fix']:
                self.stdout.write('\nAttempting to fix...')
                # Try to enable the first Google config
                google_config = SSOConfig.objects.filter(provider='google').first()
                if google_config:
                    google_config.is_active = True
                    google_config.enabled = True
                    google_config.save()
                    self.stdout.write(self.style.SUCCESS(f'✓ Enabled SSO config: {google_config.name}'))
                    clear_sso_cache()
                else:
                    self.stdout.write(self.style.ERROR('✗ No Google SSO config found to enable'))
        else:
            for config in active_sso:
                self.stdout.write(self.style.SUCCESS(f'✓ Active: {config.provider} - {config.name}'))
                
                # Validate credentials
                if not config.client_id or len(config.client_id) < 10:
                    self.stdout.write(self.style.WARNING('  ⚠ Client ID looks invalid'))
                if not config.secret_key or len(config.secret_key) < 10:
                    self.stdout.write(self.style.WARNING('  ⚠ Secret Key looks invalid'))

        # Check what get_enabled_sso_providers returns
        enabled_providers = get_enabled_sso_providers()
        self.stdout.write(f'\nget_enabled_sso_providers() returns: {enabled_providers}')

        # Check reCAPTCHA Configuration
        self.stdout.write('\n2. RECAPTCHA CONFIGURATION')
        self.stdout.write('-' * 80)
        
        recaptcha_configs = ReCaptchaConfig.objects.all()
        self.stdout.write(f'Total reCAPTCHA configs: {recaptcha_configs.count()}')
        
        active_recaptcha = ReCaptchaConfig.get_active_config()
        
        if not active_recaptcha:
            self.stdout.write(self.style.ERROR('✗ No active reCAPTCHA configuration'))
            
            if options['fix']:
                self.stdout.write('\nAttempting to fix...')
                # Try to enable the first config
                first_config = ReCaptchaConfig.objects.first()
                if first_config:
                    first_config.enabled = True
                    first_config.save()
                    self.stdout.write(self.style.SUCCESS(f'✓ Enabled reCAPTCHA config: {first_config.name}'))
                    clear_recaptcha_cache()
                else:
                    self.stdout.write(self.style.ERROR('✗ No reCAPTCHA config found to enable'))
        elif not active_recaptcha.enabled:
            self.stdout.write(self.style.ERROR(f'✗ Config exists but disabled: {active_recaptcha.name}'))
            
            if options['fix']:
                active_recaptcha.enabled = True
                active_recaptcha.save()
                self.stdout.write(self.style.SUCCESS('✓ Enabled reCAPTCHA config'))
                clear_recaptcha_cache()
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ Active: {active_recaptcha.name} (v{active_recaptcha.version})'))
            
            # Validate keys
            if not active_recaptcha.site_key or len(active_recaptcha.site_key) < 10:
                self.stdout.write(self.style.WARNING('  ⚠ Site Key looks invalid'))
            if not active_recaptcha.secret_key or len(active_recaptcha.secret_key) < 10:
                self.stdout.write(self.style.WARNING('  ⚠ Secret Key looks invalid'))

        # Check what utility functions return
        self.stdout.write(f'\nis_recaptcha_enabled() returns: {is_recaptcha_enabled()}')
        public_key = get_recaptcha_public_key()
        if public_key:
            self.stdout.write(f'get_recaptcha_public_key() returns: {public_key[:20]}...')
        else:
            self.stdout.write('get_recaptcha_public_key() returns: (empty)')

        # Test Context Processors
        self.stdout.write('\n3. CONTEXT PROCESSOR TEST')
        self.stdout.write('-' * 80)
        
        from django.test import RequestFactory
        from core.context_processors import sso_context, recaptcha_context
        
        factory = RequestFactory()
        request = factory.get('/')
        
        sso_ctx = sso_context(request)
        recaptcha_ctx = recaptcha_context(request)
        
        self.stdout.write(f'enabled_sso_providers: {sso_ctx.get("enabled_sso_providers")}')
        self.stdout.write(f'recaptcha_enabled: {recaptcha_ctx.get("recaptcha_enabled")}')
        
        if recaptcha_ctx.get('recaptcha_site_key'):
            self.stdout.write(f'recaptcha_site_key: {recaptcha_ctx.get("recaptcha_site_key")[:20]}...')
        else:
            self.stdout.write('recaptcha_site_key: (empty)')

        # Summary
        self.stdout.write('\n4. SUMMARY')
        self.stdout.write('-' * 80)
        
        issues = []
        
        if not enabled_providers:
            issues.append('No SSO providers enabled')
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ SSO providers: {", ".join(enabled_providers)}'))
        
        if not is_recaptcha_enabled():
            issues.append('reCAPTCHA not enabled')
        else:
            self.stdout.write(self.style.SUCCESS('✓ reCAPTCHA enabled'))
        
        if not public_key:
            issues.append('reCAPTCHA public key missing')
        else:
            self.stdout.write(self.style.SUCCESS('✓ reCAPTCHA public key configured'))
        
        if issues:
            self.stdout.write('\n' + self.style.ERROR('ISSUES FOUND:'))
            for issue in issues:
                self.stdout.write(self.style.ERROR(f'  ✗ {issue}'))
            
            if not options['fix']:
                self.stdout.write('\n' + self.style.WARNING('Run with --fix to attempt automatic fixes'))
        else:
            self.stdout.write('\n' + self.style.SUCCESS('✓ All configurations look good!'))
        
        self.stdout.write('\n' + self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('CHECK COMPLETE'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        if issues and not options['fix']:
            self.stdout.write('\nNext steps:')
            self.stdout.write('1. Run: python manage.py check_login_config --fix')
            self.stdout.write('2. Or manually enable configs in Django admin')
            self.stdout.write('3. Clear browser cache and restart server')
