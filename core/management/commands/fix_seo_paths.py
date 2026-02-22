"""
Django management command to fix SEO path mismatches.

This command updates PageSEO entries to match actual URL patterns.

Usage:
    python manage.py fix_seo_paths
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from core.models.seo import PageSEO


class Command(BaseCommand):
    help = 'Fixes SEO path mismatches to match actual URL patterns'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting SEO path fixes...'))
        self.stdout.write('')

        # Path corrections mapping: old_path -> new_path
        PATH_CORRECTIONS = {
            '/contact/': '/contact-us/',
            '/about/': '/about-us/',
            '/events/': '/landing/events/',  # Landing page for events
        }

        fixed_count = 0
        not_found_count = 0

        try:
            with transaction.atomic():
                self.stdout.write(self.style.HTTP_INFO('[*] Fixing SEO path mismatches...'))
                self.stdout.write('-' * 60)

                for old_path, new_path in PATH_CORRECTIONS.items():
                    try:
                        # Check if old path exists
                        seo_entry = PageSEO.objects.get(page_path=old_path)
                        
                        # Update to new path
                        seo_entry.page_path = new_path
                        seo_entry.save()
                        
                        fixed_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'  [✓] Fixed: {old_path} → {new_path}')
                        )
                    except PageSEO.DoesNotExist:
                        not_found_count += 1
                        self.stdout.write(
                            self.style.WARNING(f'  [!] Not found: {old_path}')
                        )

                # Summary
                self.stdout.write('')
                self.stdout.write('=' * 60)
                self.stdout.write(self.style.HTTP_INFO('[*] FIX SUMMARY'))
                self.stdout.write('=' * 60)
                self.stdout.write(
                    self.style.SUCCESS(f'  [✓] Fixed:     {fixed_count} path(s)')
                )
                if not_found_count > 0:
                    self.stdout.write(
                        self.style.WARNING(f'  [!] Not found: {not_found_count} path(s)')
                    )
                self.stdout.write('=' * 60)
                self.stdout.write('')
                self.stdout.write(
                    self.style.SUCCESS('[OK] SEO path fixes completed successfully!')
                )

        except Exception as e:
            self.stdout.write('')
            self.stdout.write(
                self.style.ERROR(f'✗ Error during fix: {str(e)}')
            )
            raise
