from django.core.management.base import BaseCommand
from core.models.seo import PageSEO, OrganizationSchema
from core.context_processors import DEFAULT_SEO_CONFIG


class Command(BaseCommand):
    help = 'Populate initial SEO data for high-priority pages and organization schema'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting SEO data population...'))
        
        # Create or update PageSEO objects for all high-priority pages
        pages_created = 0
        pages_updated = 0
        
        for page_path, config in DEFAULT_SEO_CONFIG.items():
            try:
                page_seo, created = PageSEO.objects.update_or_create(
                    page_path=page_path,
                    defaults={
                        'meta_title': config['title'],
                        'meta_description': config['description'],
                        'meta_keywords': config['keywords'],
                        'sitemap_priority': config['priority'],
                        'sitemap_changefreq': config['changefreq'],
                        'is_active': True,
                    }
                )
                
                if created:
                    pages_created += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Created PageSEO for: {page_path}')
                    )
                else:
                    pages_updated += 1
                    self.stdout.write(
                        self.style.WARNING(f'↻ Updated PageSEO for: {page_path}')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Error creating PageSEO for {page_path}: {e}')
                )
        
        # Create or update OrganizationSchema for NORSU
        try:
            org_schema, created = OrganizationSchema.objects.update_or_create(
                name='Negros Oriental State University Alumni System',
                defaults={
                    'logo': 'https://norsu-alumni.onrender.com/static/images/norsu-logo.png',
                    'url': 'https://norsu-alumni.onrender.com',
                    'telephone': '+63-35-422-6002',
                    'email': 'alumni@norsu.edu.ph',
                    'street_address': 'Kagawasan Avenue, Dumaguete City',
                    'address_locality': 'Dumaguete City',
                    'address_region': 'Negros Oriental',
                    'postal_code': '6200',
                    'address_country': 'PH',
                    'is_active': True,
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS('✓ Created OrganizationSchema for NORSU')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('↻ Updated OrganizationSchema for NORSU')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error creating OrganizationSchema: {e}')
            )
        
        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('SEO Data Population Complete!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f'  Pages created: {pages_created}')
        self.stdout.write(f'  Pages updated: {pages_updated}')
        self.stdout.write(f'  Total pages: {len(DEFAULT_SEO_CONFIG)}')
        self.stdout.write('')
        self.stdout.write('You can now manage SEO settings in the Django admin interface.')
        self.stdout.write('Visit /admin/core/pageseo/ to view and edit page SEO configurations.')
