from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone
from cms.models import SiteConfig
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Setup production environment with CMS data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force setup even if data already exists',
        )
        parser.add_argument(
            '--skip-cms',
            action='store_true',
            help='Skip CMS data population',
        )

    def handle(self, *args, **options):
        self.stdout.write('🚀 Starting production setup...')
        
        force = options['force']
        skip_cms = options['skip_cms']
        
        # Check if CMS data already exists
        if not force and not skip_cms:
            if SiteConfig.objects.exists():
                self.stdout.write(
                    self.style.WARNING('CMS data already exists. Use --force to overwrite.')
                )
                return
        
        try:
            # Run migrations first
            self.stdout.write('📊 Running migrations...')
            call_command('migrate', verbosity=0)
            
            # Populate CMS data
            if not skip_cms:
                self.stdout.write('📝 Populating CMS data...')
                call_command('seed_cms_data')
            
            # Create superuser if needed
            self.stdout.write('👤 Checking superuser...')
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            if not User.objects.filter(is_superuser=True).exists():
                self.stdout.write(
                    self.style.WARNING('No superuser found. Please create one manually.')
                )
            
            # Collect static files
            self.stdout.write('📁 Collecting static files...')
            call_command('collectstatic', '--noinput', verbosity=0)
            
            self.stdout.write(
                self.style.SUCCESS('✅ Production setup completed successfully!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Production setup failed: {e}')
            )
            logger.error(f'Production setup failed: {e}')
            raise
