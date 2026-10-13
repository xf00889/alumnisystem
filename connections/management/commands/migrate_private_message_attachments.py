"""Copy old message files out of publicly served MEDIA_ROOT, verify, then optionally purge.

Back up the database and media before running; deploy an Nginx/Apache deny rule
for /media/connections/messages/ BEFORE executing this migration.
"""
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.db.models import Q

from connections.models import DirectMessage
from core.file_validators import sanitize_filename


class Command(BaseCommand):
    help = 'Move existing public message attachments to private storage.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--delete-legacy', action='store_true', help='Delete public original only after verified private copy.')

    def handle(self, *args, **options):
        inspected = moved = missing = failed = removed = 0
        for message in DirectMessage.objects.exclude(Q(attachment='') | Q(attachment__isnull=True)).iterator(chunk_size=200):
            inspected += 1
            legacy_name = message.attachment.name
            if message.attachment.storage.exists(legacy_name):
                continue  # Already moved to private storage.
            if not legacy_name.startswith('connections/messages/') or not default_storage.exists(legacy_name):
                missing += 1
                self.stderr.write(f'Missing legacy attachment for message {message.pk}')
                continue
            if options['dry_run']:
                self.stdout.write(f'Would migrate message {message.pk}')
                continue
            try:
                legacy_size = default_storage.size(legacy_name)
                with default_storage.open(legacy_name, 'rb') as source:
                    message.attachment.save(legacy_name.split('/')[-1], source, save=False)
                if not message.attachment.storage.exists(message.attachment.name) or message.attachment.size != legacy_size:
                    raise OSError('Private copy size mismatch')
                message.attachment_display_name = sanitize_filename(message.attachment_display_name or legacy_name)
                message.save(update_fields=['attachment', 'attachment_display_name'])
                moved += 1
                if options['delete_legacy']:
                    # Do not purge an original still used by another message.
                    if not DirectMessage.objects.filter(attachment=legacy_name).exists():
                        default_storage.delete(legacy_name)
                        removed += 1
            except Exception as exc:
                failed += 1
                self.stderr.write(f'Failed migrating message {message.pk}: {exc}')
        self.stdout.write(f'Inspected: {inspected}, moved: {moved}, missing: {missing}, failed: {failed}, removed public originals: {removed}')
        if missing or failed:
            raise SystemExit(1)
