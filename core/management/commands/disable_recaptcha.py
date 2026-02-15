"""
Management command to disable reCAPTCHA
"""
from django.core.management.base import BaseCommand
from core.models.recaptcha_config import ReCaptchaConfig
from core.recaptcha_utils import clear_recaptcha_cache


class Command(BaseCommand):
    help = 'Disable reCAPTCHA by creating/updating database configuration'

    def handle(self, *args, **options):
        # Get or create reCAPTCHA configuration
        config, created = ReCaptchaConfig.objects.get_or_create(
            is_active=True,
            defaults={
                'name': 'Default Configuration',
                'enabled': False,
                'version': 'v3',
                'site_key': '',
                'secret_key': '',
                'threshold': 0.5
            }
        )
        
        if not created:
            # Update existing configuration to disable it
            config.enabled = False
            config.save()
            self.stdout.write(self.style.SUCCESS('reCAPTCHA has been disabled (updated existing configuration)'))
        else:
            self.stdout.write(self.style.SUCCESS('reCAPTCHA has been disabled (created new configuration)'))
        
        # Clear cache to ensure changes take effect immediately
        clear_recaptcha_cache()
        self.stdout.write(self.style.SUCCESS('reCAPTCHA cache cleared'))
