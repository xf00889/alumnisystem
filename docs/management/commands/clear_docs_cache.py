"""
Django management command to clear documentation TOC cache.

Usage:
    python manage.py clear_docs_cache
"""

from django.core.management.base import BaseCommand
from docs.navigation import NavigationBuilder


class Command(BaseCommand):
    help = 'Clear the documentation table of contents cache'

    def handle(self, *args, **options):
        """Clear the TOC cache"""
        nav_builder = NavigationBuilder()
        nav_builder.invalidate_cache()
        self.stdout.write(
            self.style.SUCCESS('Successfully cleared documentation TOC cache')
        )

