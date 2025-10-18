"""
Management command to load CMS fixtures from JSON files.
This provides an alternative way to seed the database with predefined content.
"""
import os
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.conf import settings


class Command(BaseCommand):
    help = 'Load CMS fixtures from JSON files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fixtures-dir',
            type=str,
            default='cms/fixtures/',
            help='Directory containing fixture files (default: cms/fixtures/)',
        )
        parser.add_argument(
            '--fixture-files',
            nargs='+',
            help='Specific fixture files to load (e.g., site_config.json features.json)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before loading fixtures',
        )

    def handle(self, *args, **options):
        fixtures_dir = options['fixtures_dir']
        fixture_files = options.get('fixture_files', [])
        clear = options.get('clear', False)
        
        self.stdout.write(
            self.style.SUCCESS(f'📦 Loading CMS fixtures from {fixtures_dir}...')
        )

        # If no specific files provided, load all JSON files in the directory
        if not fixture_files:
            if not os.path.exists(fixtures_dir):
                raise CommandError(f'Fixtures directory {fixtures_dir} does not exist')
            
            fixture_files = [
                f for f in os.listdir(fixtures_dir) 
                if f.endswith('.json') and not f.startswith('__')
            ]
            
            if not fixture_files:
                self.stdout.write(
                    self.style.WARNING(f'No JSON fixture files found in {fixtures_dir}')
                )
                return

        # Clear existing data if requested
        if clear:
            self.stdout.write('🗑️  Clearing existing CMS data...')
            # Note: This would need to be implemented carefully to avoid foreign key issues
            self.stdout.write(
                self.style.WARNING('Clear functionality not implemented for safety. Use --force with seed_cms_content instead.')
            )

        # Load each fixture file
        for fixture_file in fixture_files:
            fixture_path = os.path.join(fixtures_dir, fixture_file)
            
            if not os.path.exists(fixture_path):
                self.stdout.write(
                    self.style.WARNING(f'Fixture file {fixture_path} not found, skipping...')
                )
                continue
            
            try:
                self.stdout.write(f'📥 Loading {fixture_file}...')
                call_command('loaddata', fixture_path, verbosity=0)
                self.stdout.write(f'✅ Successfully loaded {fixture_file}')
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error loading {fixture_file}: {e}')
                )

        self.stdout.write(
            self.style.SUCCESS('✅ CMS fixtures loading completed!')
        )
