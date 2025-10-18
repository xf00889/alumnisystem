"""
Management command to create Django fixtures from existing CMS content.
This is useful for creating backup fixtures or for manual data loading.
"""
import os
import json
from django.core.management.base import BaseCommand
from django.core import serializers
from django.conf import settings
from cms.models import (
    SiteConfig, PageSection, StaticPage, StaffMember, 
    TimelineItem, ContactInfo, FAQ, Feature, Testimonial
)


class Command(BaseCommand):
    help = 'Create Django fixtures from existing CMS content'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default='cms/fixtures/',
            help='Directory to save fixture files (default: cms/fixtures/)',
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'xml', 'yaml'],
            default='json',
            help='Fixture format (default: json)',
        )

    def handle(self, *args, **options):
        output_dir = options['output_dir']
        format_type = options['format']
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        self.stdout.write(
            self.style.SUCCESS(f'📦 Creating CMS fixtures in {output_dir}...')
        )

        # Define models to export
        models_to_export = [
            (SiteConfig, 'site_config'),
            (PageSection, 'page_sections'),
            (StaticPage, 'static_pages'),
            (StaffMember, 'staff_members'),
            (TimelineItem, 'timeline_items'),
            (ContactInfo, 'contact_info'),
            (FAQ, 'faqs'),
            (Feature, 'features'),
            (Testimonial, 'testimonials'),
        ]

        for model_class, filename in models_to_export:
            try:
                # Get all objects from the model
                objects = model_class.objects.all()
                
                if objects.exists():
                    # Create fixture file
                    fixture_file = os.path.join(output_dir, f'{filename}.{format_type}')
                    
                    # Serialize objects
                    serialized_data = serializers.serialize(format_type, objects, indent=2)
                    
                    # Write to file
                    with open(fixture_file, 'w', encoding='utf-8') as f:
                        f.write(serialized_data)
                    
                    self.stdout.write(f'✅ Created {fixture_file} ({objects.count()} objects)')
                else:
                    self.stdout.write(f'⏭️  No {model_class.__name__} objects found, skipping...')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error creating fixture for {model_class.__name__}: {e}')
                )

        self.stdout.write(
            self.style.SUCCESS('✅ CMS fixtures creation completed!')
        )
