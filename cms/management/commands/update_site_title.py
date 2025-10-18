from django.core.management.base import BaseCommand
from cms.models import SiteConfig, PageSection


class Command(BaseCommand):
    help = 'Update both site config tagline and hero section title to keep them in sync'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tagline',
            type=str,
            help='New tagline/title for the site',
            required=True
        )

    def handle(self, *args, **options):
        tagline = options['tagline']
        
        # Update Site Config
        site_config = SiteConfig.get_site_config()
        site_config.site_tagline = tagline
        site_config.save()
        
        # Update Hero Section
        hero_section = PageSection.objects.filter(
            section_type='hero', 
            is_active=True
        ).first()
        
        if hero_section:
            hero_section.title = tagline
            hero_section.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated both site config tagline and hero section title to: "{tagline}"'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'Updated site config tagline to: "{tagline}" but no active hero section found'
                )
            )
