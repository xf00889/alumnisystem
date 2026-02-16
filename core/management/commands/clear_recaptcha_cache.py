"""
Management command to clear reCAPTCHA cache
"""
from django.core.management.base import BaseCommand
from django.core.cache import cache


class Command(BaseCommand):
    help = 'Clear reCAPTCHA configuration cache'

    def handle(self, *args, **options):
        self.stdout.write('Clearing reCAPTCHA cache...')
        
        # Clear the reCAPTCHA config cache
        cache.delete('recaptcha_active_config')
        
        # Also clear any related cache keys
        cache_keys = [
            'recaptcha_active_config',
            'recaptcha_public_key',
            'recaptcha_private_key',
        ]
        
        for key in cache_keys:
            cache.delete(key)
        
        self.stdout.write(self.style.SUCCESS('✓ reCAPTCHA cache cleared successfully!'))
        self.stdout.write('')
        self.stdout.write('You can now verify the status with:')
        self.stdout.write('  python manage.py shell -c "from core.recaptcha_utils import is_recaptcha_enabled; print(f\'reCAPTCHA enabled: {is_recaptcha_enabled()}\')"')
