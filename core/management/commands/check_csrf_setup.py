"""Diagnose CSRF cookie configuration for the URL used in a browser."""
from urllib.parse import urlsplit
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Check CSRF/session cookie settings for a browser URL (no secrets printed)."

    def add_arguments(self, parser):
        parser.add_argument('--url', default='http://127.0.0.1:8000',
                            help='Browser URL, including scheme and port')

    def handle(self, *args, **options):
        browser_url = options['url']
        parsed = urlsplit(browser_url)
        if parsed.scheme not in ('http', 'https') or not parsed.hostname:
            raise CommandError('Provide a full http:// or https:// URL.')
        self.stdout.write(f'Browser origin: {parsed.scheme}://{parsed.netloc}')
        self.stdout.write(f'DEBUG: {settings.DEBUG}')
        self.stdout.write(f'CSRF_COOKIE_SECURE: {settings.CSRF_COOKIE_SECURE}')
        self.stdout.write(f'SESSION_COOKIE_SECURE: {settings.SESSION_COOKIE_SECURE}')
        self.stdout.write(f'CSRF_COOKIE_HTTPONLY: {settings.CSRF_COOKIE_HTTPONLY}')
        self.stdout.write(f'CSRF_COOKIE_SAMESITE: {settings.CSRF_COOKIE_SAMESITE}')
        self.stdout.write(f'CSRF_COOKIE_DOMAIN: {settings.CSRF_COOKIE_DOMAIN}')
        self.stdout.write(f'CSRF_COOKIE_PATH: {settings.CSRF_COOKIE_PATH}')
        if parsed.scheme == 'http' and (settings.CSRF_COOKIE_SECURE or settings.SESSION_COOKIE_SECURE):
            self.stderr.write(self.style.ERROR(
                'HTTP + Secure cookies: browser may not send the CSRF/session cookie. '
                'Use HTTPS for production, or a development configuration with secure cookies '
                'disabled for local HTTP only. Never disable CSRF middleware.'))
            raise CommandError('Cookie security settings are incompatible with the browser URL.')
        self.stdout.write(self.style.SUCCESS(
            'Cookie scheme appears compatible. Use only one hostname consistently '
            '(127.0.0.1 and localhost do not share cookies).'))
