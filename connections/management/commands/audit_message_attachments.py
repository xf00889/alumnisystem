"""Read-only audit of chat attachment storage. Never displays private URLs or tokens."""
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from django.db.models import Q

from connections.models import DirectMessage


class Command(BaseCommand):
    help = "Count available private/legacy/missing message attachments without exposing files."

    def handle(self, *args, **kwargs):
        counts = {'private': 0, 'legacy': 0, 'missing': 0, 'error': 0}
        query = DirectMessage.objects.exclude(Q(attachment='') | Q(attachment__isnull=True))
        for message in query.iterator(chunk_size=200):
            try:
                name = message.attachment.name
                if message.attachment.storage.exists(name):
                    counts['private'] += 1
                elif name.startswith('connections/messages/') and default_storage.exists(name):
                    counts['legacy'] += 1
                else:
                    counts['missing'] += 1
            except (OSError, ValueError, AttributeError):
                counts['error'] += 1
        for key, value in counts.items():
            self.stdout.write(f'{key}: {value}')
        self.stdout.write('No files were modified. Back up both media storage and the database before migration.')
