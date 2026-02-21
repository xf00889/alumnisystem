from django.core.management.base import BaseCommand
from cms.models import SiteConfig


class Command(BaseCommand):
    help = 'Update site config tagline'

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
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated site config tagline to: "{tagline}"'
            )
        )
