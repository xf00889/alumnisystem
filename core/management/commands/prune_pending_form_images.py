"""Remove expired temporary image uploads left by abandoned admin forms."""
from datetime import timedelta

from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Prune temporary event/campaign images older than one day.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Only report candidates')

    def handle(self, *args, **options):
        prefix = 'pending-form-images'
        removed = 0
        try:
            _, filenames = default_storage.listdir(prefix)
        except (OSError, NotImplementedError, FileNotFoundError):
            self.stdout.write('Temporary image folder is empty or listing is unsupported.')
            return
        cutoff = timezone.now() - timedelta(days=1)
        for filename in filenames:
            # Only direct image files created by this application are eligible.
            if '/' in filename or not filename.endswith(('.jpg', '.png', '.webp')):
                continue
            path = f'{prefix}/{filename}'
            try:
                if default_storage.get_modified_time(path) >= cutoff:
                    continue
                if not options['dry_run']:
                    default_storage.delete(path)
                removed += 1
            except (OSError, NotImplementedError):
                continue
        self.stdout.write(f'{removed} expired temporary image(s) ' +
                          ('eligible for removal.' if options['dry_run'] else 'removed.'))
